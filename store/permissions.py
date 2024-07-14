from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrStaffOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_object_permission(self, request, view, obj):
        # работает на тех вью в которых передаётся ссылка на объект: get(id), put(id), delete(id) запросах
        # условие and obj.owner == request.user, разрешение на все методы запросов если юзер из запроса и owner совпали
        return bool(
            request.method in SAFE_METHODS or
            request.user and
            request.user.is_authenticated and (obj.owner == request.user or request.user.is_staff)
        )
