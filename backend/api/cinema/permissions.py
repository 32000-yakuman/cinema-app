from rest_framework.permissions import BasePermission


class IsCounterStaff(BasePermission):
    """
    窓口職員のみ許可する権限クラス
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_staff_member", False)
        )

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )