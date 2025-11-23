"""
Accounts Model views
"""

import json
import logging

from django.contrib.auth import authenticate, login, logout, password_validation
from django.core.validators import validate_email
from django.forms import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import User
from core.helper import is_token_valid, decode_uid
from core.date import convert_to_string

from .api.serializer import UserSerializer
from .notification import send_password_reset_email
from .forms import SignUpForm, LoginForm
from .eums import ThemeEnum

logger = logging.getLogger("MainProcess")


def get_user_by_uid(uid):
    try:
        user = User.objects.get(pk=uid)
        return user
    except User.DoesNotExist:
        return None


@csrf_exempt
def ajax_login(request):
    """
    Function that handles login request
    """
    if request.method == "POST":
        data = json.loads(request.body)
        form = LoginForm(data)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse(
                    {"status": "success", "msg": "Login successful"}, status=200
                )
            else:
                return JsonResponse(
                    {"status": "fail", "msg": "Invalid username or password"},
                    status=200,
                )
        else:
            return JsonResponse(
                {"status": "fail", "msg": "Invalid username or password"}, status=200
            )
    return JsonResponse({"status": "fail", "msg": "Invalid request method"}, status=405)


@csrf_exempt
def signup(request):
    """
    Functions that handles when user submits the signup request
    """
    errors = {}
    if request.method == "POST":
        data = json.loads(request.body)
        form = SignUpForm(data)
        if form.is_valid():
            form.save()
            return JsonResponse(
                {"status": "success", "msg": "Signup successfully", "errors": errors},
                status=200,
            )
        else:
            if form.errors:
                errors = form.errors
    return JsonResponse(
        {"status": "fail", "msg": "Invalid request method", "errors": errors},
        status=200,
    )


@csrf_exempt
def session_update(request):
    """
    Functions that check if user is session is still valid
    """
    if request.method == "GET":
        logger.info("cookies here.......%s", request.COOKIES)
        if request.user.is_authenticated:
            user_data = UserSerializer(request.user)
            profile = {
                **user_data.data,
                "cover": request.build_absolute_uri(user_data.data.get("cover")),
                "profile_image": request.build_absolute_uri(user_data.data.get("profile_image")),
                "thumbnail": request.build_absolute_uri(user_data.data.get("thumbnail")),
            }
            return JsonResponse(
                {
                    "status": "success",
                    "msg": "Login successful",
                    "isAuthenticated": True,
                    "profile": profile,
                    "theme_mode": request.user.theme_mode,
                    "notification_count": 0
                },
                status=200,
            )
        else:
            return JsonResponse(
                {
                    "status": "fail",
                    "msg": f"Invalid credentials {request.user}",
                    "isAuthenticated": False,
                    "notification_count": 0,
                },
                status=200,
            )
    return JsonResponse(
        {"status": "fail", "msg": "Invalid request method", "is_authenticated": False},
        status=405,
    )


@csrf_exempt
def ajax_logout(request):
    """
    Handles logout request
    """
    if request.method == "POST":
        logout(request)
        return JsonResponse(
            {"msg": "Successfully logged out", "status": "success"}, status=200
        )
    return JsonResponse({"msg": "Invalid request method", "status": "fail"}, status=400)


@csrf_exempt
def change_password(request):
    """
    Function that handles change password request
    """
    status = "fail"
    msg = "Invalid request method"
    if request.method == "POST":
        data = json.loads(request.body)
        new_password1 = data.get("new_password1")
        new_password2 = data.get("new_password2")
        uidb64 = data.get("uid")
        token = data.get("token")
        if not new_password1 and not new_password2:
            msg = "Fill in the required fields."
        elif new_password1 and new_password2 and new_password1 != new_password2:
            msg = "Password Mismatch"
        elif not uidb64 or not token:
            msg = "No valid request token"
        else:
            uid = decode_uid(uidb64)
            user = get_user_by_uid(uid)
            if user is None or not is_token_valid(user, token):
                msg = "Invalid request"
            else:
                try:
                    password_validation.validate_password(new_password1, user=user)
                except ValidationError as error:
                    msg = error.messages
                else:
                    user.set_password(new_password1)
                    user.save()
                    status = "success"
                    msg = "Successfully updated the password"
    return JsonResponse({"msg": msg, "status": status}, status=200)


@csrf_exempt
def validate_password_reset_request(request):
    """
    Function that is triggered when user validates the link after the forgot password is submitted
    """
    status = "fail"
    msg = "Invalid request method"
    if request.method == "POST":
        data = json.loads(request.body)
        uidb64 = data.get("uid")
        token = data.get("token")
        if not uidb64 or not token:
            msg = "Invalid request"
        else:
            uid = decode_uid(uidb64)
            user = get_user_by_uid(uid)
            if user is not None and is_token_valid(user, token):
                status = "success"
                msg = "Valid request"
            else:
                msg = "Invalid request"
    return JsonResponse({"msg": msg, "status": status}, status=200)


@csrf_exempt
def forgot_password(request):
    """
    Function that is triggered when user submit the forgot password request
    """
    status = "fail"
    msg = "Invalid request method"
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        if not email:
            msg = "Email is required"
        else:
            try:
                validate_email(email)
            except ValidationError as e:
                msg = f"{e.message}"
            else:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    msg = "Email address does not exists"
                else:
                    status = "success"
                    send_password_reset_email(user)
                    msg = "A link to reset your password has been emailed to you if an account exists for this address."
    return JsonResponse({"msg": msg, "status": status}, status=200)



def update_profile(request):
    """
    Function to change user theme mode
    """
    if request.method == "POST":
        status = "error"
        msg = "error"
        if request.user.is_authenticated:
            post_data = json.loads(request.body)
            if post_data and post_data.get("last_updated"):
                client_last_updated = post_data.get("last_updated")
                server_last_updated = convert_to_string(request.user.last_updated)
                if client_last_updated != server_last_updated:
                    msg = "Data may be outdated. Refresh to ensure accuracy."
                    for field, value in post_data.items():
                        post_data[field] = getattr(request.user, field)
                    post_data["last_updated"] = server_last_updated
                else:
                    for field, value in post_data.items():
                        if (
                            hasattr(request.user, field)
                            and field in request.user.editable_fields
                        ):
                            if getattr(request.user, field) != value:
                                setattr(request.user, field, value)
                                request.user.save()
                            else:
                                msg = "invalid field"
                    post_data["last_updated"] = convert_to_string(
                        request.user.last_updated
                    )
                    msg = "Updated successfully"
                    status = "success"
            return JsonResponse(
                {"status": status, "msg": msg, "data": post_data}, status=200
            )
    return JsonResponse(
        {"status": "fail", "msg": "Invalid request method", "is_authenticated": False},
        status=405,
    )


def update_profile_image(request):
    """
    Function to update user profile image or cover photo.
    """
    if request.method != "POST":
        return JsonResponse(
            {
                "status": "fail",
                "msg": "Invalid request method",
                "is_authenticated": False,
            },
            status=405,
        )

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": "error",
                "msg": "User not authenticated",
                "is_authenticated": False,
            },
            status=401,
        )

    post_data = {k: v for k, v in request.POST.items()}
    if not post_data or "last_updated" not in post_data:
        return JsonResponse(
            {"status": "error", "msg": "Missing required data"}, status=400
        )

    client_last_updated = post_data["last_updated"]
    server_last_updated = convert_to_string(request.user.last_updated)

    if client_last_updated != server_last_updated:
        return JsonResponse(
            {
                "status": "error",
                "msg": "Data may be outdated. Refresh to ensure accuracy.",
                "data": {
                    "last_updated": server_last_updated,
                    "profile_image": request.build_absolute_uri(
                        request.user.profile_image
                    ),
                    "cover": request.build_absolute_uri(request.user.cover),
                },
            },
            status=409,
        )

    if request.FILES:
        return handle_file_upload(request, post_data)
    elif "cover" in post_data and post_data["cover"] == "null":
        return remove_cover_photo(request, post_data)
    elif "profile_image" in post_data and post_data["profile_image"] == "null":
        return remove_profile_photo(request, post_data)

    return JsonResponse(
        {"status": "error", "msg": "No valid action performed"}, status=400
    )


def handle_file_upload(request, post_data):
    """
    Handles file upload for profile image or cover photo.
    """
    if "profile_image" in request.FILES:
        return update_profile_photo(request, post_data)
    elif "cover" in request.FILES:
        return update_cover_photo(request, post_data)

    return JsonResponse(
        {"status": "error", "msg": "No valid file uploaded"}, status=400
    )


def update_profile_photo(request, post_data):
    """
    Updates the user's profile photo.
    """
    try:
        image = request.FILES["profile_image"]
        request.user.profile_image = image
        request.user.save()
        request.user.create_thumbnail()
        post_data["last_updated"] = convert_to_string(request.user.last_updated)
        post_data["profile_image"] = request.build_absolute_uri(
            request.user.profile_image
        )
        return JsonResponse(
            {
                "status": "success",
                "msg": "Successfully updated your profile photo",
                "data": post_data,
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "msg": f"Failed to update profile photo: {str(e)}"},
            status=500,
        )


def update_cover_photo(request, post_data):
    """
    Updates the user's cover photo.
    """
    try:
        cover_photo = request.FILES["cover"]
        request.user.cover = cover_photo
        request.user.save()
        post_data["last_updated"] = convert_to_string(request.user.last_updated)
        post_data["cover"] = request.build_absolute_uri(request.user.cover)
        return JsonResponse(
            {
                "status": "success",
                "msg": "Successfully updated your cover photo",
                "data": post_data,
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "msg": f"Failed to update cover photo: {str(e)}"},
            status=500,
        )


def remove_cover_photo(request, post_data):
    """
    Removes the user's cover photo.
    """
    try:
        request.user.cover = None
        request.user.save()
        post_data["cover"] = None
        return JsonResponse(
            {
                "status": "success",
                "msg": "Successfully removed cover photo",
                "data": post_data,
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "msg": f"Failed to remove cover photo: {str(e)}"},
            status=500,
        )


def remove_profile_photo(request, post_data):
    """
    Removes the user's profile photo.
    """
    try:
        request.user.profile_image = None
        request.user.thumbnail = None
        request.user.save()
        post_data["profile_image"] = None
        return JsonResponse(
            {
                "status": "success",
                "msg": "Successfully removed profile photo",
                "data": post_data,
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "msg": f"Failed to remove profile photo: {str(e)}"},
            status=500,
        )


if not settings.IS_PROD:
    update_profile = csrf_exempt(update_profile)
    update_profile_image = csrf_exempt(update_profile_image)
