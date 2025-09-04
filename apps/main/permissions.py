from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет только авторам объекта редактировать его.
    Предполагается, что экземпляр модели имеет атрибут `author`.
    """
    
    def has_object_permission(self, request, view, obj):
        # Разрешения на чтение предоставляются для любого запроса,
        # поэтому мы всегда разрешаем GET, HEAD или OPTIONS запросы.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешения на запись предоставляются только владельцу объекта.
        return obj.author == request.user