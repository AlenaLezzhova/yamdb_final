from django.contrib import admin

from .models import User


class UserAdmin(admin.ModelAdmin):
    """
    Администрирование ролей пользователей.
    """
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'bio', 'role',
    )


admin.site.register(User, UserAdmin)
