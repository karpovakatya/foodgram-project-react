# Generated by Django 3.2.16 on 2024-01-27 16:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_remove_shoppingcart_pub_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredientrecipe',
            options={'verbose_name': 'Ингредиенты в рецепте', 'verbose_name_plural': 'Ингредиенты в рецепте'},
        ),
    ]