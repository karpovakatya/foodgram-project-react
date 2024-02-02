from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core import constants
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

from .filters import RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeCreateUpdateDeleteSerializer,
    RecipeData,
    RecipeSerializer,
    SubscribeSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UsersSerializer,
)

User = get_user_model()


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

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
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        check_user = User.objects.filter(id=id)
        if not check_user.exists():
            return Response(
                {"detail": "Нельзя подписатся на несуществующего автора"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SubscribeSerializer(
            data={"user": self.request.user.id, "author": id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        check_user = User.objects.filter(id=id)
        current_user = self.request.user
        check_subscribe = Subscription.objects.filter(
            user=current_user, author=id
        )
        if not check_user.exists():
            return Response(
                {"detail": "Нельзя отписатся от несуществующего автора"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if check_subscribe.exists():
            check_subscribe.delete()
            return Response(
                {"detail": "Вы отписались от автора"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"detail": "Вы уже отписаны от автора"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateDeleteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        user = request.user

        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ingredients = (
            IngredientRecipe.objects.filter(
                recipe__shopping_cart__user=request.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
        )

        shopping_list = 'Список покупок\n'
        shopping_list += '\n'.join(
            [
                f'- {ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measurement_unit"]})'
                f' - {ingredient["amount"]}'
                for ingredient in ingredients
            ]
        )

        filename = constants.FILENAME
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Авторизованный пользователь добавляет/удаляет рецепт в избранном"""

        if request.method == 'POST':
            self.recipe_check(pk)
            return self.adding(Favorite, request.user, pk)

        if request.method == 'DELETE':
            get_object_or_404(Recipe, pk=pk)
            return self.deleting(Favorite, request.user, pk)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        """Авторизованный пользователь добавляет/удаляет рецепт в список"""

        if request.method == 'POST':
            self.recipe_check(pk)
            return self.adding(ShoppingCart, request.user, pk)

        if request.method == 'DELETE':
            get_object_or_404(Recipe, pk=pk)
            return self.deleting(ShoppingCart, request.user, pk)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def recipe_check(self, pk):
        if not Recipe.objects.filter(pk=pk).exists():
            raise ValidationError(
                {'detail': 'Рецепт с указанным ID не найден.'}
            )

    def adding(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен в избранное'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipe = Recipe.objects.get(pk=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeData(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def deleting(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт не был добавлен'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('name',)
    search_fields = ('name',)
