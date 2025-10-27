from __future__ import annotations

from django.contrib.auth import get_user_model

from .models import Request, StaffProfile

User = get_user_model()


def get_staff_profile(user: User | None) -> StaffProfile | None:
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        profile, _ = StaffProfile.objects.get_or_create(
            user=user,
            defaults={"role": StaffProfile.Role.ADMIN},
        )
        return profile
    return getattr(user, "staff_profile", None)


def user_can_view_request(user: User, request: Request) -> bool:
    profile = get_staff_profile(user)
    if not profile:
        return False
    if profile.role == StaffProfile.Role.ADMIN:
        return True
    if profile.role == StaffProfile.Role.EMPLOYEE:
        return profile.department_id and profile.department_id == request.department_id
    return False


def user_can_edit_request(user: User, request: Request) -> bool:
    profile = get_staff_profile(user)
    if not profile:
        return False
    if profile.role == StaffProfile.Role.ADMIN:
        return True
    if profile.role == StaffProfile.Role.EMPLOYEE:
        return profile.department_id and profile.department_id == request.department_id
    return False

