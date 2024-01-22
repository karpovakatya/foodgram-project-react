from django.contrib.auth.models import AbstractUser
from django.db import models

from backend import settings


class User(AbstractUser):
    """Переопределяем модель User.

    Переопределили поля password и email.
    Остальные поля наследуем от класса AbstractUser как есть,
    так как они удовлетворяют требованиям.
    """

    email = models.EmailField(
        verbose_name='e-mail',
        max_length=settings.EMAIL_MAX_LENGHT,
        unique=True
    )
    password = models.CharField(
        verbose_name='password',
        max_length=settings.PASSWORD_MAX_LENGHT
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.email


class Subscription(models.Model):
    """Подписки"""

    # кто подписан (пользователь)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    # на кого подписан (автор рецептов)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='Автор рецептов'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_sibscription'
            )
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
