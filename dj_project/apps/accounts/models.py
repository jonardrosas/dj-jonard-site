"""Extending auth User"""

from django.contrib.auth.models import (
    AbstractUser,
    UserManager,
    GroupManager,
    Group,
    Permission,
)
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.conf import settings
from core.helper import create_thumbnail
from .eums import ThemeEnum


class GroupProfileManager(GroupManager):

    def get_queryset(self) -> models.QuerySet:
        queryset = super().get_queryset()
        return queryset.filter(profile__is_active=True)


class GroupProfile(models.Model):
    group = models.OneToOneField(
        Group, on_delete=models.CASCADE, primary_key=True, related_name="profile"
    )
    image = models.ImageField(upload_to="groups/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    objects = GroupProfileManager()


class AccountManager(UserManager):

    def get_queryset(self) -> models.QuerySet:
        queryset = super().get_queryset()
        return queryset.filter(is_active=True)


class User(AbstractUser):
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
    cover = models.ImageField(
        upload_to="thumbnails/", default="profile_pics/default_cover_photo.webp"
    )
    theme_mode = models.CharField(max_length=50, default=ThemeEnum.DEFAULT.value)
    objects = AccountManager()
    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="account_set",
        related_query_name="account",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="account_set",
        related_query_name="account",
    )
    is_deleted = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    editable_fields = [
        "first_name",
        "last_name",
        "cover",
        "profile_picture",
        "theme_mode",
    ]

    @property
    def profile_image(self):
        """Will return saved profile or default image"""
        if not self.profile_picture:
            return None
            # return static("accounts/images/default_profile.jpg")
        return f"{settings.MEDIA_URL}{self.profile_picture.name}"

    @profile_image.setter
    def profile_image(self, val):
        self.profile_picture = val
        return

    def create_thumbnail(self):
        create_thumbnail(self.profile_picture, "thumbnail", self, "thumbnails")

    def notification_count(self):
        return self.history_notification.filter(is_read=False).count()


class UserChangeHistory(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="change_history"
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="changed_users",
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    field_changed = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Change in {self.field_changed} for {self.user.username} by {self.changed_by.username if self.changed_by else 'system'}"
