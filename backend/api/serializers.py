from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    StringRelatedField,
    PrimaryKeyRelatedField,
    StringRelatedField,
)

from recipes.models import (
    Recipe,
    # IngredientRecipe,
    Ingredient,
    Tag
)
from users.models import Subscription

User = get_user_model()


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class UsersCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class UsersSerializer(UserSerializer):
    """Вывод данных пользователя"""

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
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'count', 'recipes'
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
            return Subscription.objects.filter(user=user, author=obj).exists()

        def get_recipes_count(self, obj):
            return obj.author.recipes.count()

        def get_recipes(self, obj):
            request = self.context.get('request')
            limit = request.GET.get('recipes_limit')
            recipes = obj.author.recipes.all()
            if limit:
                recipes = recipes[:int(limit)]
            serializer = RecipeBaseSerializer(recipes, many=True, read_only=True)
            return serializer.data


class RecipeBaseSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')