from django.contrib.auth.models import Group
from django.db.models import Exists, Q
from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_gestor(user):
    return user.is_authenticated and user.groups.filter(name="gestores").exists()


def for_owner_or_gestor(queryset, user, owner_lookup):
    gestor_membership = Group.user_set.through.objects.filter(
        user_id=user.pk, group__name="gestores"
    )
    return queryset.filter(Exists(gestor_membership) | Q(**{owner_lookup: user}))


class IsGestor(BasePermission):
    def has_permission(self, request, view):
        return is_gestor(request.user)


class IsGestorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            # Keep catalogue browsing public; only writes require the gestor role.
            return True
        return is_gestor(request.user)


class IsOwnerOrGestor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return is_gestor(request.user) or obj.customer.user_id == request.user.id


class IsCustomerOwnerOrGestor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return is_gestor(request.user) or obj.user_id == request.user.id
