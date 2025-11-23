import json
import pdb
from copy import copy
from django.forms import ImageField
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import ImageField
from rest_framework.utils import model_meta
from rest_framework.settings import api_settings
from ..models import User, GroupProfile
from ..eums import PASSWORD_NOT_MATCH


class ProfileImageSerializer(ImageField):
    pass


class GroupProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupProfile
        fields = ("image", "is_active")


class UserGroupSerializer(serializers.ModelSerializer):
    profile = GroupProfileSerializer(required=False)
    image = serializers.SerializerMethodField()

    class Meta:

        model = Group
        fields = ("id", "name", "profile", "image")

    def to_internal_value(self, data):
        return data
        if data:
            return data.get("id")
        return data

    def get_image(self, instance):
        request = self.context.get("request")
        if hasattr(instance, "profile"):
            if instance.profile.image and request:
                return request.build_absolute_uri(instance.profile.image.url)
        return None


class AccountImage(ImageField):
    pass


class UserBaseSerializer(serializers.ModelSerializer):
    thumbnail = AccountImage()

    class Meta:
        """Base Account Meta"""

        model = User
        fields = [
            "theme_mode",
            "username",
            "id",
            "first_name",
            "last_name",
            "is_superuser",
            "is_staff",
            "date_joined",
            "email",
            "profile_image",
            "profile_picture",
            "cover",
            "thumbnail",
        ]


class UserSerializer(UserBaseSerializer):
    """
    Base User Serializer
    """

    email = serializers.EmailField(required=True)
    groups = UserGroupSerializer(required=False, many=True)

    class Meta:
        """Base Account Meta"""

        model = User
        fields = [
            "theme_mode",
            "username",
            "id",
            "first_name",
            "last_name",
            "is_superuser",
            "is_staff",
            "date_joined",
            "email",
            "profile_image",
            "cover",
            "groups",
            "thumbnail",
            "last_updated",
        ]


class UserCreateSerializer(UserBaseSerializer):
    profile_image = ProfileImageSerializer(required=False, allow_null=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        """Base Account Meta"""

        model = User
        fields = [
            "theme_mode",
            "username",
            "id",
            "first_name",
            "last_name",
            "is_superuser",
            "is_staff",
            "date_joined",
            "password",
            "confirm_password",
            "email",
            "profile_image",
        ]

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            profile_picture=validated_data.get("profile_image"),
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(PASSWORD_NOT_MATCH)
        return data


class UserEditSerializer(serializers.ModelSerializer):
    """
    Base User Serializer
    """

    email = serializers.EmailField(required=True)
    profile_image = ProfileImageSerializer(required=False)
    groups = UserGroupSerializer(many=True, required=False)

    class Meta:
        """Base Account Meta"""

        model = User
        fields = [
            "theme_mode",
            "username",
            "id",
            "first_name",
            "last_name",
            "is_superuser",
            "is_staff",
            "email",
            "is_superuser",
            "is_staff",
            "profile_image",
            "groups",
        ]

    def to_internal_value(self, old_data):
        old_data = old_data.copy()
        if old_data.get("profile_image"):
            if (
                isinstance(old_data.get("profile_image"), str)
                and old_data.get("profile_image") == "null"
            ):
                old_data.pop("profile_image")

        data = super().to_internal_value(old_data)
        if old_data.get("groups"):
            data["groups"] = [
                group["id"] for group in json.loads(old_data.get("groups"))
            ]
        print(old_data)
        print(data)
        return data

    def update(self, instance, validated_data):
        info = model_meta.get_field_info(instance)
        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)
        instance.save()
        for _attr, _values in m2m_fields:
            old_values = getattr(instance, _attr).values_list("id", flat=True)
            for _value in _values:
                relation_ins = info.relations[_attr].related_model.objects.get(
                    id=_value
                )
                related_field = getattr(instance, _attr)
                related_field.add(relation_ins)
            for _value in old_values:
                if _value not in _values:
                    relation_ins = info.relations[_attr].related_model.objects.get(
                        id=_value
                    )
                    related_field = getattr(instance, _attr)
                    related_field.remove(relation_ins)
        return instance


class PermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permission
        fields = ("id", "name", "codename")

    def to_internal_value(self, data):
        return data.get("id")


class GroupSerializer(serializers.ModelSerializer):
    profile = GroupProfileSerializer(required=False)
    permissions = PermissionSerializer(many=True, required=False)
    members = UserBaseSerializer(many=True, source="account_set", required=False)

    class Meta:

        model = Group
        fields = ("id", "name", "profile", "permissions", "members")

    def to_internal_value(self, data):
        final_data = {
            "name": data.get("name"),
        }
        if data.get("profile__image"):
            if not isinstance(data.get("profile__image"), str):
                final_data["profile"] = {"image": data.get("profile__image")}
            elif (
                isinstance(data.get("profile__image"), str)
                and data.get("profile__image") == "null"
            ):
                final_data["profile"] = {"image": None}
        if data.get("permissions"):
            final_data["permissions"] = [
                {**permission} for permission in json.loads(data["permissions"])
            ]
        return super().to_internal_value(final_data)

    def create(self, validated_data):
        group, is_created = Group.objects.get_or_create(name=validated_data.get("name"))
        if is_created:
            group_ins, is_profile_created = GroupProfile.objects.get_or_create(
                group=group,
            )
            if validated_data.get("permissions"):
                permissions = validated_data["permissions"]
                for permission in permissions:
                    permission_ins = Permission.objects.get(id=permission)
                    group.permissions.add(permission_ins)
            if validated_data.get("profile") and validated_data["profile"]["image"]:
                group_ins.image = validated_data["profile"]["image"]
                group_ins.save()
        return group

    def update(self, instance, validated_data):
        if instance.name != validated_data.get("name"):
            instance.name = validated_data.get("name")
            instance.save()
        if validated_data.get("permissions"):
            permissions = validated_data["permissions"]
            old_permissions = instance.permissions.values_list("id", flat=True)

            for permission in permissions:
                permission_ins = Permission.objects.get(id=permission)
                instance.permissions.add(permission_ins)
            for permission in old_permissions:
                if permission not in permissions:
                    permission_ins = Permission.objects.get(id=permission)
                    instance.permissions.remove(permission_ins)
        else:
            instance.permissions.clear()

        if validated_data.get("profile") and "image" in validated_data["profile"]:
            group_ins, is_profile_created = GroupProfile.objects.get_or_create(
                group=instance,
            )
            group_ins.image = validated_data["profile"]["image"]
            group_ins.save()
        return instance


class UserProfileSerializer(UserBaseSerializer):
    groups = GroupSerializer(many=True)

    class Meta:
        model = User
        fields = [
            "theme_mode",
            "username",
            "id",
            "first_name",
            "last_name",
            "is_superuser",
            "is_staff",
            "date_joined",
            "email",
            "profile_image",
            "groups",
        ]
