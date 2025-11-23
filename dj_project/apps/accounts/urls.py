from django.urls import path, include
from .views import (
    ajax_login,
    session_update,
    ajax_logout,
    change_password,
    forgot_password,
    validate_password_reset_request,
    signup,
    update_profile,
    update_profile_image,
)
from .router import router

urlpatterns = [
    path("api/v2/", include(router.urls)),
    path("login/", ajax_login, name="ajax_login"),
    path("proceed_login/", ajax_login, name="ajax_login2"),
    path("lg/", ajax_login, name="ajax_login3"),
    path("session_update/", session_update, name="session_update"),
    path("signup/", signup, name="signup"),
    path("logout/", ajax_logout, name="ajax_logout"),
    path("out/", ajax_logout, name="ajax_logout3"),
    path("change_password/", change_password, name="change_password"),
    path("forgot_password/", forgot_password, name="forgot_password"),
    path("update_profile/", update_profile, name="update_profile"),
    path("update_profile_image/", update_profile_image, name="update_profile_image"),
    path(
        "validate_password_reset_request/",
        validate_password_reset_request,
        name="validate_password_reset_request",
    ),
]