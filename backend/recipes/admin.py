from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import (
    Recipe, Ingredient, Tag, IngredientRecipe, Favorite, ShoppingCart
)


@admin.register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('name', 'id', 'author')
    # readonly_fields = ('added_in_favorites',)
    # list_filter = ('author', 'name', 'tags',)

    # @display(description='Количество в избранных')
    # def added_in_favorites(self, obj):
    #     return obj.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'color', 'slug',)


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(ModelAdmin):
    list_display = ('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
