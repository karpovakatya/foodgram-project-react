from django.contrib.auth.models import AbstractUser
from django.db import models

from core import constants


class User(AbstractUser):
    """Переопределяем модель User."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        verbose_name='e-mail',
        unique=True
    )
    first_name = models.CharField(
        max_length=constants.NAME_MAX_LENGHT,
        blank=False
    )
    last_name = models.CharField(
        max_length=constants.NAME_MAX_LENGHT,
        blank=False
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('email', 'username')

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

    def __str__(self):
        return f'{self.user} {self.author}'
