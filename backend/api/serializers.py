from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    SerializerMethodField,
    ReadOnlyField,
    CharField,
)
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Favorite, Ingredient, IngredientRecipe, Recipe, Tag
from users.models import Subscription

User = get_user_model()


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UsersSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(request
                    and request.user.is_authenticated
                    and Subscription.objects.filter(
                        user=request.user.id, author=obj.id).exists())


class SubscribeSerializer(UserSerializer):
    class Meta:
        model = Subscription
        fields = (
            'user',
            'author',
        )

    def validate(self, data):
        if data['user'] == data['author']:
            raise ValidationError(
                {'detail': 'Нельзя подписатся на самого себя'}
            )
        if Subscription.objects.filter(
            user=data['user'], author=data['author']
        ).exists():
            raise ValidationError(
                {'detail': 'Вы уже подписанны на этого автора'}
            )
        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(instance.user, context=self.context).data


class SubscriptionSerializer(ModelSerializer):
    # recipes_count = ReadOnlyField(source="recipes.count")
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes_count',
            'recipes',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(request
                    and request.user.is_authenticated
                    and Subscription.objects.filter(
                        user=request.user.id, author=obj.id).exists())

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        try:
            if limit:
                limit = int(limit)
                recipes = recipes[:limit]
        except ValueError:
            raise ValueError('limit должен быть целым числом')
        serializer = RecipeData(recipes, many=True, read_only=True)
        return serializer.data


class RecipeData(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientRecipeSerializer(ModelSerializer):
    id = IntegerField(write_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UsersSerializer(read_only=True)
    image = SerializerMethodField(read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredient_recipe__amount')
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()


class RecipeCreateUpdateDeleteSerializer(ModelSerializer):
    ingredients = IngredientRecipeSerializer(many=True)
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    author = UsersSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def to_representation(self, instance):
        request = self.context.get("request")
        serializer = RecipeSerializer(
            instance, context={"request": request}
        )
        return serializer.data

    @transaction.atomic
    def add_ingredients(self, ingredients, recipe):
        IngredientRecipe.objects.bulk_create(
            IngredientRecipe(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.add_ingredients(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            IngredientRecipe.objects.filter(recipe=instance).delete()
            ingredients = validated_data.pop('ingredients')
            self.add_ingredients(ingredients, instance)

        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.set(tags)

        return super().update(instance, validated_data)

    def validate(self, data):
        tags = data.get('tags')
        # image = data.get('image')
        ingredients = data.get('ingredients')
        if not ingredients:
            raise ValidationError('Добавьте ингредиенты')
        if not tags:
            raise ValidationError('Укажите хотя бы один тег')
        # if not image:
        #     raise ValidationError('Изображение не предоставлено')

        if len(tags) != len(set(tags)):
            raise ValidationError(
                'Теги не должны дублироваться'
            )

        ingredients = [
            ingredient.get('id') for ingredient in data.get('ingredients')
        ]
        if len(ingredients) != len(set(ingredients)):
            raise ValidationError(
                'Ингредиенты не должны дублироваться'
            )
        return data


# class FavoriteSerializer(ModelSerializer):
#     class Meta:
#         model = Favorite
#         fields = (
#             'recipe',
#             'user',
#         )
#         validators = [
#             UniqueTogetherValidator(
#                 queryset=Favorite.objects.all(),
#                 fields=('recipe', 'user'),
#                 message='Рецепт уже добавлен в избранное',
#             )
#         ]

#     def to_representation(self, instance):
#         return RecipeData(
#             instance.recipe, context=self.context
#         ).data
