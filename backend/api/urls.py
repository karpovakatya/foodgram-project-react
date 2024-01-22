from django.urls import include, path
from rest_framework import routers

from .views import (
    UserViewSet,
    TagViewSet,
    RecipeViewSet,
    IngredientViewSet,
)

app_name = 'api'

router = routers.DefaultRouter()

router.register('users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('recipes', RecipeViewSet, basename='recipe')
router.register('ingredients', IngredientViewSet, basename='ingredient')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
