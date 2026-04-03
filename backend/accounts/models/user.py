from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
    AbstractUser,
)
from django.db import models

from common.constant.user import UserStatusEnum
from common.models.base import DateTimeModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.UserRole.SUPER_ADMIN)
        extra_fields.setdefault("status", User.UserStatus.ACTIVE)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, PermissionsMixin, DateTimeModel):
    PORTAL_PERMISSION_KEYS = (
        "manage_restaurant_profile",
        "manage_bookings",
        "manage_tables",
        "manage_menu",
        "manage_orders",
        "manage_payments",
        "manage_team",
        "view_reports",
    )
    ADMIN_PERMISSION_KEYS = PORTAL_PERMISSION_KEYS

    class SocialProvider(models.TextChoices):
        GOOGLE = "google", "google"
        APPLE = "apple", "apple"
        FACEBOOK = "facebook", "facebook"
        NONE = "none", "none"

    class UserRole(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "SUPER_ADMIN"
        ADMIN = "ADMIN", "ADMIN"
        WAITER = "WAITER", "WAITER"
        CASHIER = "CASHIER", "CASHIER"
        USER = "USER", "USER"

    class UserStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "ACTIVE"
        INACTIVE = "INACTIVE", "INACTIVE"
        BLOCKED = "BLOCKED", "BLOCKED"

    username = None
    first_name = None
    last_name = None
    groups = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=256, null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    social_provider = models.CharField(
        max_length=32, choices=SocialProvider.choices, default=SocialProvider.NONE
    )
    status = models.CharField(choices=UserStatus.choices, default=UserStatus.INACTIVE)
    role = models.CharField(choices=UserRole.choices, default=UserRole.USER)
    admin_permissions = models.JSONField(default=dict, blank=True)
    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    @property
    def is_staff(self):
        return self.role in [self.UserRole.ADMIN, self.UserRole.SUPER_ADMIN]

    @property
    def is_superuser(self):
        return self.role in [self.UserRole.SUPER_ADMIN]

    @property
    def has_portal_access(self):
        return (
            self.is_active
            and self.status == self.UserStatus.ACTIVE
            and self.role
            in [
                self.UserRole.ADMIN,
                self.UserRole.WAITER,
                self.UserRole.CASHIER,
                self.UserRole.SUPER_ADMIN,
            ]
        )

    @property
    def effective_permissions(self):
        if self.role == self.UserRole.SUPER_ADMIN:
            return {key: True for key in self.PORTAL_PERMISSION_KEYS}

        if self.role not in [self.UserRole.ADMIN, self.UserRole.WAITER, self.UserRole.CASHIER]:
            return {key: False for key in self.PORTAL_PERMISSION_KEYS}

        return self.build_permissions_payload(self.admin_permissions, self.role)

    @property
    def effective_admin_permissions(self):
        return self.effective_permissions

    @classmethod
    def get_role_default_permissions(cls, role):
        defaults = {key: False for key in cls.PORTAL_PERMISSION_KEYS}

        if role == cls.UserRole.SUPER_ADMIN:
            return {key: True for key in cls.PORTAL_PERMISSION_KEYS}

        role_defaults = {
            cls.UserRole.ADMIN: {
                "manage_restaurant_profile": True,
                "manage_bookings": True,
                "manage_tables": True,
                "manage_menu": True,
                "manage_orders": True,
                "manage_payments": True,
            },
            cls.UserRole.WAITER: {
                "manage_tables": True,
                "manage_orders": True,
            },
            cls.UserRole.CASHIER: {
                "manage_orders": True,
                "manage_payments": True,
            },
        }
        defaults.update(role_defaults.get(role, {}))
        return defaults

    @classmethod
    def build_permissions_payload(cls, permissions=None, role=None):
        normalized = cls.get_role_default_permissions(role)
        stored_permissions = permissions or {}

        for key in cls.PORTAL_PERMISSION_KEYS:
            if key in stored_permissions:
                normalized[key] = bool(stored_permissions.get(key, False))

        return normalized

    def has_permission(self, permission_key: str) -> bool:
        return bool(self.effective_permissions.get(permission_key, False))

    def has_admin_permission(self, permission_key: str) -> bool:
        return self.has_permission(permission_key)

    class Meta:
        db_table = "users"
