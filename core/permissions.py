from rest_framework.permissions import BasePermission


class IsEmployeePermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not request.user.is_employee:
            return False
        return True


class IsCustomerPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated or request.user.is_employee:
            return False
        return True


class IsAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated or request.user.is_admin:
            return False
        return True
