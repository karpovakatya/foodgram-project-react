from django.db.models import F
from django.db import transaction
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.validators import UniqueTogetherValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    StringRelatedField,
    PrimaryKeyRelatedField,
    IntegerField,
)
from recipes.models import (
    Recipe,
    IngredientRecipe,
    Ingredient,
    Tag,
    Favorite,
)
from users.models import Subscription

User = get_user_model()


class UsersCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


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
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


class SubscriptionSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(source='author.id', read_only=True)
    email = StringRelatedField(source='author.email')
    username = StringRelatedField(source='author.username')
    first_name = StringRelatedField(source='author.first_name')
    last_name = StringRelatedField(source='author.last_name')
    is_subscribed = SerializerMethodField(read_only=True)
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta:
        model = Subscription
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
        read_only_fields = ('author',)
        validators = [UniqueTogetherValidator(
                      queryset=Subscription.objects.all(),
                      fields=['user', 'author']
                      )]

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user, author=obj.author
        ).exists()

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.author.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeData(recipes, many=True, read_only=True)
        return serializer.data


class RecipeData(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UsersSerializer(read_only=True)
    image = Base64ImageField()
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


class IngredientRecipeSerializer(ModelSerializer):
    id = IntegerField(write_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeCreateUpdateDeleteSerializer(ModelSerializer):
    ingredients = IngredientRecipeSerializer(
        many=True,
    )
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

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError({
                'ingredients': 'Добавьте ингредиенты'
            })
        ingredients_list = []
        for ingredient in value:
            if 'id' not in ingredient or 'amount' not in ingredient:
                raise ValidationError({
                    'ingredients': 'Не указано количество или id ингредиента'
                })
            id = ingredient['id']

            if not Ingredient.objects.filter(id=id).exists():
                raise ValidationError({
                    'ingredients': f"Ингредиент с id={id} не существует"
                })

            if ingredient in ingredients_list:
                raise ValidationError({
                    'ingredients': 'Ингредиенты дублируются'
                })

            if int(ingredient['amount']) <= 0:
                raise ValidationError({
                    'amount': 'Укажите количество больше 0'
                })

            ingredients_list.append(ingredient)
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError({
                'tags': 'Укажите хотя бы один тег'
            })
        tags_list = []
        for tag in value:
            if tag in tags_list:
                raise ValidationError({
                    'tags': 'Теги не должны дублироваться'
                })
            tags_list.append(tag)
        return value

    def validate_image(self, value):
        if not value:
            raise ValidationError({
                    'image': 'Изображение не предоставлено'
                })
        return value

    @transaction.atomic
    def add_ingredients(self, recipe, ingredients):
        IngredientRecipe.objects.bulk_create(
            IngredientRecipe(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated):
        tags = validated.pop('tags')
        ingredients = validated.pop('ingredients')
        recipe = Recipe.objects.create(**validated)
        recipe.tags.set(tags)
        self.add_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context['request'].user

        if instance.author != user:
            raise PermissionDenied(
                {'message': 'Вы не являетесь автором рецепта.'}
            )

        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if ingredients is None:
            raise ValidationError({'ingredients': 'Это поле обязательно.'})

        if tags is None:
            raise ValidationError({'tags': 'Это поле обязательно.'})

        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.add_ingredients(instance, ingredients)

        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data


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
