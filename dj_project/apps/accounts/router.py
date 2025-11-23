from rest_framework import routers
from .api.viewsets import (
    AuthViewset,
    GroupViewSets,
    PermissionViewSets,
    UserAccountViewSets,
    UserGroupViewSets,
    UserProfileViewSets,
)

router = routers.DefaultRouter()
router.register(r"auth", AuthViewset, basename="auth")
router.register(r"users", UserAccountViewSets, basename="users")
router.register(r"profile", UserProfileViewSets, basename="profile")
router.register(r"groups", GroupViewSets)
router.register(r"user-group", UserGroupViewSets, basename="user-group")
router.register(r"permissions", PermissionViewSets)
