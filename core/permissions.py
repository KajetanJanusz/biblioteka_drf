from rest_framework.permissions import BasePermission


class IsEmployeePermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return not request.user.is_employee and request.user.is_active


class IsCustomerPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_employee and request.user.is_active


class IsAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return not request.user.is_admin and request.user.is_active
