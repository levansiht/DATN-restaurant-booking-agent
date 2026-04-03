from rest_framework import serializers
from accounts.models.user import User
from rest_framework.exceptions import APIException

from accounts.models.user_info import UserInfo


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ["phone_number", "address"]


class UserSerializer(serializers.ModelSerializer):
    is_set_password = serializers.SerializerMethodField()
    user_info = UserInfoSerializer(read_only=True)
    admin_permissions = serializers.SerializerMethodField()
    portal_permissions = serializers.SerializerMethodField()
    has_portal_access = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "status",
            "role",
            "admin_permissions",
            "portal_permissions",
            "has_portal_access",
            "is_set_password",
            "user_info",
        ]
        read_only_fields = ["id"]

    def get_is_set_password(self, obj):
        return (
            obj.password is not None
            and obj.password != ""
            and obj.social_provider == User.SocialProvider.GOOGLE
        )

    def get_admin_permissions(self, obj):
        return obj.effective_permissions

    def get_portal_permissions(self, obj):
        return obj.effective_permissions

    def get_has_portal_access(self, obj):
        return obj.has_portal_access


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise APIException("Current password is incorrect")
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class UpdateUserSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=False)
    address = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ["full_name", "phone_number", "address"]

    def update(self, instance, validated_data):
        instance.full_name = validated_data.get("full_name", instance.full_name)
        user_info = UserInfo.objects.filter(user=instance).first()
        if user_info is None:
            user_info = UserInfo.objects.create(user=instance)

        user_info.phone_number = validated_data.get(
            "phone_number", user_info.phone_number
        )
        user_info.address = validated_data.get("address", user_info.address)
        user_info.save()
        instance.save()
        return instance


class UserBaseInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "email"]
