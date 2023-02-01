from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Права администратора."""
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and (request.user.is_staff or request.user.is_admin))


class IsAdminOrReadOnly(permissions.BasePermission):
    """Администратор или только чтение."""
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or (request.user.is_authenticated
                    and (request.user.is_staff or request.user.is_admin)))


class IsAuthorOrAdminOrModerator(permissions.BasePermission):
    """Автор, Администратор или Модератор."""
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user
                and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.user and request.user.is_authenticated
                and (request.user.is_staff or request.user.is_admin
                     or request.user.is_moderator
                     or obj.author == request.user or request.method == 'POST'
                     and request.user.is_authenticated)
                or (request.method in permissions.SAFE_METHODS))
