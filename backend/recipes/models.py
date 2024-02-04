from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    ForeignKey,
    ImageField,
    ManyToManyField,
    Model,
    PositiveSmallIntegerField,
    SlugField,
    TextField,
    UniqueConstraint,
)

from core import constants

User = get_user_model()


class Ingredient(Model):
    """Ингредиент"""

    name = CharField(
        'Ингредиент',
        max_length=constants.INGREDIENT_NAME_MAX_LENGHT,
        unique=True
    )
    measurement_unit = CharField(
        'Единицы измерения',
        max_length=constants.MES_UNIT_NAME_MAX_LENGHT
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name', )
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'], name='ingredient'
            )
        ]

    def __str__(self):
        return self.name


class Tag(Model):
    """Теги"""

    name = CharField(
        'Тег',
        max_length=constants.TAG_NAME_MAX_LENGHT,
        unique=True
    )
    color = ColorField(
        'Цвет',
        max_length=constants.TAG_COLOR_MAX_LENGHT,
        unique=True
    )
    slug = SlugField(
        'Уникальный слаг',
        max_length=constants.TAG_SLUG_MAX_LENGHT,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('slug', )

    def __str__(self):
        return self.name


class Recipe(Model):
    """Рецепт"""

    author = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = CharField('Название', max_length=constants.RECIPE_NAME_MAX_LENGHT)
    text = TextField('Описание', blank=False)
    pub_date = DateTimeField(
        'Дата и время публикации',
        auto_now_add=True
    )
    image = ImageField(
        'Фото',
        upload_to='recipes/images/'
    )
    cooking_time = PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                constants.MIN_VALUE,
                message=('Время приготовления не может быть менее '
                         f'{constants.MIN_VALUE} минуты')
            ),
            MaxValueValidator(
                constants.MAX_VALUE,
                message=('Время приготовления не может быть больше '
                         f'{constants.MAX_VALUE} минут')
            )
        ]
    )
    ingredients = ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipies',
        verbose_name='Ингредиенты'
    )
    tags = ManyToManyField(
        Tag,
        blank=False,
        related_name='recipes',
        verbose_name='Теги'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )

    def __str__(self):
        return self.name


class IngredientRecipe(Model):
    """Промежуточная модель связывает ингредиент и рецепт"""

    ingredient = ForeignKey(
        Ingredient,
        on_delete=CASCADE,
        related_name='ingredient_recipe'
    )
    recipe = ForeignKey(
        Recipe,
        on_delete=CASCADE,
        related_name='ingredient_recipe'
    )
    amount = PositiveSmallIntegerField(
        'Количество',
        default=constants.DEFAULT_AMOUNT,
        validators=[
            MinValueValidator(
                constants.MIN_VALUE_AMOUNT,
                message=('Количество должно быть не меньше '
                         f'{constants.MIN_VALUE_AMOUNT}')
            ),
            MaxValueValidator(
                constants.MAX_VALUE_AMOUNT,
                message=('Количество не может быть больше '
                         f'{constants.MAX_VALUE_AMOUNT}')
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return (f'{self.ingredient.name} '
                f'({self.ingredient.measurement_unit}) - '
                f'{self.amount}')


class Favorite(Model):
    """Избранное"""

    user = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = ForeignKey(
        Recipe,
        on_delete=CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'], name='favorite')
        ]

    def str(self):
        return f'{self.user} {self.recipe}'


class ShoppingCart(Model):
    """Список покупок"""

    user = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = ForeignKey(
        Recipe,
        on_delete=CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'], name='shopping_cart')
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'
