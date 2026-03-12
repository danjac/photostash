from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from photostash.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """User model admin."""
