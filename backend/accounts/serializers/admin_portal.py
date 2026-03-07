from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from accounts.models.user import User
from accounts.models.user_info import UserInfo
from accounts.serializers.user import UserSerializer


def normalize_admin_permissions(permissions):
    permissions = permissions or {}
    return {
        key: bool(permissions.get(key, False))
        for key in User.ADMIN_PERMISSION_KEYS
    }


class AdminPortalUserSerializer(UserSerializer):
    phone_number = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["phone_number"]

    def get_phone_number(self, obj):
        user_info = getattr(obj, "user_info", None)
        return user_info.phone_number if user_info else None


class AdminUserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=256)
    password = serializers.CharField(min_length=8)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    admin_permissions = serializers.JSONField(required=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email này đã tồn tại.")
        return value

    def validate_admin_permissions(self, value):
        return normalize_admin_permissions(value)

    def create(self, validated_data):
        phone_number = validated_data.pop("phone_number", None)
        permissions = validated_data.pop("admin_permissions", {})
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
            role=User.UserRole.ADMIN,
            status=User.UserStatus.ACTIVE,
            is_active=True,
            social_provider=User.SocialProvider.NONE,
            admin_permissions=permissions,
        )
        UserInfo.objects.update_or_create(
            user=user,
            defaults={"phone_number": phone_number},
        )
        return user


class AdminUserUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=256, required=False)
    password = serializers.CharField(min_length=8, required=False)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.ChoiceField(choices=User.UserStatus.choices, required=False)
    admin_permissions = serializers.JSONField(required=False)

    def validate_admin_permissions(self, value):
        return normalize_admin_permissions(value)

    def update(self, instance, validated_data):
        phone_number = validated_data.pop("phone_number", None)
        password = validated_data.pop("password", None)
        permissions = validated_data.pop("admin_permissions", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.password = make_password(password)

        if permissions is not None:
            instance.admin_permissions = permissions

        instance.is_active = instance.status == User.UserStatus.ACTIVE
        instance.save()

        if phone_number is not None:
            UserInfo.objects.update_or_create(
                user=instance,
                defaults={"phone_number": phone_number},
            )

        return instance
