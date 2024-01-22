from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.db.models import UniqueConstraint
from django.db.models import (
    Model,
    ForeignKey,
    CharField,
    TextField,
    DateTimeField,
    ImageField,
    ManyToManyField,
    SmallIntegerField,
    SlugField,
    CASCADE,
)

User = get_user_model()


class Ingredient(Model):
    """Ингредиент"""

    name = CharField(
        'Ингредиент',
        max_length=200
    )
    measurement_unit = CharField(
        'Единицы измерения',
        max_length=200
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name', )

    def __str__(self):
        return self.name


class Tag(Model):
    """Теги"""

    name = CharField(
        'Тег',
        max_length=200
    )
    color = CharField(
        'Цвет в HEX',
        max_length=7
    )
    slug = SlugField(
        'Уникальный слаг',
        unique=True,
        max_length=200
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('slug', )

    def __str__(self):
        return self.name


class Recipe(Model):
    """Рецепт"""

    name = CharField('Название', max_length=200)
    text = TextField('Описание')
    pub_date = DateTimeField(
        'Дата и время публикации',
        auto_now_add=True
    )
    image = ImageField(
        'Фото',
        upload_to='media/',
        null=True,
        blank=True
    )
    author = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='recipies',
        verbose_name='Автор рецепта'
    )
    cooking_time = SmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[MinValueValidator(1)]
    )
    ingredients = ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipies',
        verbose_name='Ингредиенты'
    )
    tags = ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )

    def __str__(self):
        return self.text


class IngredientRecipe(Model):
    """Промежуточная модель связывает ингредиент и рецепт"""
    ingredient = ForeignKey(Ingredient, on_delete=CASCADE)
    recipe = ForeignKey(Recipe, on_delete=CASCADE)

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        ordering = ('recipe', )

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class Favorite(Model):
    """Избранное"""

    user = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='user_favorites',
        verbose_name='Пользователь',
    )
    recipe = ForeignKey(
        Recipe,
        on_delete=CASCADE,
        related_name='recipe_favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'], name='favorite')
        ]

    def str(self):
        return self.user


class ShoppingCart(Model):
    """Список покупок"""

    user = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='user_shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = ForeignKey(
        Recipe,
        on_delete=CASCADE,
        related_name='recipe_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'], name='shopping_cart')
        ]

    def __str__(self):
        return self.user
