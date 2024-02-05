from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    SerializerMethodField,
)
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
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


class UsersSerializer(ModelSerializer):
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
        return bool(
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user.id, author=obj.id
            ).exists()
        )


class SubscribeSerializer(ModelSerializer):
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


class SubscriptionSerializer(UsersSerializer):
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta:
        model = User
        fields = UsersSerializer.Meta.fields + ('recipes_count', 'recipes',)

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        try:
            if limit:
                recipes = recipes[:int(limit)]
        except ValueError:
            raise ValueError('limit должен быть целым числом')
        serializer = RecipeData(recipes, many=True, read_only=True)
        return serializer.data


class RecipeData(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientRecipeSerializer(ModelSerializer):
    id = IntegerField(write_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise ValidationError(f'Ингредиент с id={value} не существует')
        return value


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
        request = self.context.get('request')
        user = request.user
        return bool(
            request
            and request.user.is_authenticated
            and user.favorites.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user
        return bool(
            request
            and request.user.is_authenticated
            and user.shopping_cart.filter(recipe=obj).exists()
        )


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
        request = self.context.get('request')
        serializer = RecipeSerializer(
            instance, context={'request': request}
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
        IngredientRecipe.objects.filter(recipe=instance).delete()
        ingredients = validated_data.pop('ingredients')
        self.add_ingredients(ingredients, instance)

        tags = validated_data.pop('tags')
        instance.tags.set(tags)

        return super().update(instance, validated_data)

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredients')
        if not ingredients:
            raise ValidationError('Добавьте ингредиенты')

        if not tags:
            raise ValidationError('Укажите хотя бы один тег')

        if len(tags) != len(set(tags)):
            raise ValidationError(
                'Теги не должны дублироваться'
            )

        ingredients_list = []
        for ingredient in ingredients:
            if ingredient in ingredients_list:
                raise ValidationError(
                    'Ингредиенты не должны дублироваться'
                )
            ingredients_list.append(ingredient)

        return data


class FavoriteSerializer(ModelSerializer):
    class Meta:
        model = Favorite
        fields = (
            'recipe',
            'user',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('recipe', 'user'),
                message='Рецепт уже добавлен в избранное',
            )
        ]

    def to_representation(self, instance):
        return RecipeData(
            instance.recipe, context=self.context
        ).data


class ShoppingCartSerializer(ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = (
            'recipe',
            'user',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('recipe', 'user'),
                message='Рецепт уже добавлен в корзину',
            )
        ]

    def to_representation(self, instance):
        return RecipeData(
            instance.recipe, context=self.context
        ).data
