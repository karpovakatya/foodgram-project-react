from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from djoser.views import UserViewSet
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from django_filters.rest_framework import DjangoFilterBackend
from .pagination import CustomPagination
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from recipes.models import (
    # Favorite,
    Ingredient,
    # IngredientRecipe,
    # Recipe,
    # ShoppingCart,
    Tag)
from users.models import Subscription
from .serializers import (
    UsersSerializer,
    SubscriptionSerializer,
    TagSerializer,
    IngredientSerializer,
)

User = get_user_model()

APPLY_METHODS = (
    'get',
    'post',
    'patch',
    'delete',
)


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Авторизованный пользователь получает список своих подписок"""
        user = request.user
        queryset = Subscription.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages,
            many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        serializer_class=SubscriptionSerializer,
    )
    def subscribe(self, request, **kwargs):
        """Авторизованный пользователь подписался/отписался по id автора рецепта"""
        user = request.user
        id = self.kwargs.get('id')
        author = get_object_or_404(User, id=id)

        if user == author:
            return Response({
                'errors': 'Нельзя подписаться на самого себя'
            }, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            subscription, _ = Subscription.objects.get_or_create(
                user=user, author=author)
            serializer = self.get_serializer(
                subscription, context={'request': request}
            )
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            Subscription.objects.filter(
                user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(ModelViewSet):
    pass


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    # filterset_class = IngredientFilter
