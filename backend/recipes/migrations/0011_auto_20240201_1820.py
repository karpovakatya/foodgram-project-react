# Generated by Django 3.2.16 on 2024-02-01 15:20

import colorfield.fields
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0010_auto_20240128_1458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientrecipe',
            name='amount',
            field=models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1, message='Количество должно быть не меньше 1')], verbose_name='Количество'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, message='Время не может быть менее 1 минуты'), django.core.validators.MaxValueValidator(32000, message='Время приготовления слишком большое')]),
        ),
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=colorfield.fields.ColorField(default='#FFFFFF', image_field=None, max_length=7, samples=None, unique=True, verbose_name='Цвет'),
        ),
        migrations.AddConstraint(
            model_name='ingredient',
            constraint=models.UniqueConstraint(fields=('name', 'measurement_unit'), name='ingredient'),
        ),
    ]
