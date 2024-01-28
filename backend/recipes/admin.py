from django.contrib import admin
from django.contrib.admin import ModelAdmin, display

from .models import (
    Recipe,
    Ingredient,
    Tag,
    IngredientRecipe,
    Favorite,
    ShoppingCart
)


@admin.register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('name', 'id', 'author', 'add_in_favorites')
    search_fields = ('author', 'name',)
    list_filter = ('tags',)

    @display(description='Добавили в избранное')
    def add_in_favorites(self, obj):
        return Favorite.objects.filter(recipe=obj.id).count()


@admin.register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    search_fields = ('name',)


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(ModelAdmin):
    list_display = ('recipe', 'ingredient')
    search_fields = ('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('recipe',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('recipe',)
