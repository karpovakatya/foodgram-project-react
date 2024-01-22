from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import User


@admin.register(User)
class UserInAdmin(ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
