import pdb
import json
from django.conf import settings
from django.db.models import Count
from django.contrib.auth.models import Group, Permission
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from django.core.validators import validate_email
from core.drf.authenticators import CsrfExemptSessionAuthentication
from django.contrib.auth import authenticate, login, logout, password_validation
from core.helper import is_token_valid, decode_uid
from django.forms import ValidationError
from .serializer import (
    PermissionSerializer,
    UserSerializer,
    UserEditSerializer,
    UserCreateSerializer,
    GroupSerializer,
    UserProfileSerializer,
    UserGroupSerializer,
)
from .permissions import AccountPermission
from .filters import GroupFilter, UserFilter
from ..models import User
from ..forms import LoginForm, SignUpForm
from ..eums import PASSWORD_NOT_MATCH, ThemeEnum
from ..notification import send_password_reset_email


def get_user_by_uid(uid):
    try:
        user = User.objects.get(pk=uid)
        return user
    except User.DoesNotExist:
        return None


class AuthViewset(ModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_authenticators(self):
        if not settings.IS_PROD:
            return [CsrfExemptSessionAuthentication()]
        return super().get_authenticators()

    @action(detail=False, methods=["post"])
    def login(self, request):
        data = request.data
        form = LoginForm(data)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return Response(
                    {"status": "success", "msg": "Login successful"}, status=200
                )
            else:
                return Response(
                    {"status": "fail", "msg": "Invalid username or password"},
                    status=200,
                )
        else:
            return Response(
                {"status": "fail", "msg": "Invalid username or password"}, status=200
            )

    @action(detail=False, methods=["post"])
    def logout(self, request):
        logout(request)
        return Response(
            {"msg": "Successfully logged out", "status": "success"}, status=200
        )


    @action(detail=False, methods=["post"])
    def signup(self, request):
        """
        Functions that handles when user submits the signup request
        """
        errors = {}
        data = request.data
        form = SignUpForm(data)
        if form.is_valid():
            form.save()
            return Response(
                {"status": "success", "msg": "Signup successfully", "errors": errors},
                status=200,
            )
        else:
            if form.errors:
                errors = form.errors
        return Response(
            {"status": "fail", "msg": "Invalid request method", "errors": errors},
            status=200,
        )

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        """
        Function that handles change password request
        """
        _status = "fail"
        msg = "Invalid request method"
        data = request.data
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
                    _status = "success"
                    msg = "Successfully updated the password"
        return Response({"msg": msg, "status": _status}, status=200)


    @action(detail=False, methods=["post"])
    def validate_password_reset_request(self, request):
        """
        Function that is triggered when user validates the link after the forgot password is submitted
        """
        _status = "fail"
        msg = "Invalid request method"
        data = request.data
        uidb64 = data.get("uid")
        token = data.get("token")
        if not uidb64 or not token:
            msg = "Invalid request"
        else:
            uid = decode_uid(uidb64)
            user = get_user_by_uid(uid)
            if user is not None and is_token_valid(user, token):
                _status = "success"
                msg = "Valid request"
            else:
                msg = "Invalid request"
        return Response({"msg": msg, "status": _status}, status=200)

    @action(detail=False, methods=["post"])
    def forgot_password(self, request):
        """
        Function that is triggered when user submit the forgot password request
        """
        _status = "fail"
        msg = "Invalid request method"
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
                    _status = "success"
                    send_password_reset_email(user)
                    msg = "A link to reset your password has been emailed to you if an account exists for this address."
        return Response({"msg": msg, "status": _status}, status=200)

    @action(detail=False, methods=["post"])
    def change_theme_mode(self, request):
        """
        Function to change user theme mode
        """

        data = request.data
        theme = data.get('theme')            
        if request.user.is_authenticated:
            request.user.theme_mode = theme
            request.user.save()
            return Response({"theme_mode": theme}, status=200)
        else:
            return Response({"theme_mode": theme}, status=200)


class UserAccountViewSets(ModelViewSet):
    """Base User ViewSet"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AccountPermission]
    filterset_class = UserFilter
    filterset_fields = (
        "theme_mode",
        "username",
        "id",
        "first_name",
        "last_name",
        "email",
        "is_staff",
        "is_superuser",
        "groups",
    )
    search_fields = (
        "theme_mode",
        "username",
        "id",
        "first_name",
        "last_name",
        "email",
    )

    def get_authenticators(self):
        if not settings.IS_PROD:
            return [CsrfExemptSessionAuthentication()]
        return super().get_authenticators()

    def perform_create(self, serializer):
        super().perform_create(serializer)
        serializer.instance.create_thumbnail()

    def create(self, request, *args, **kwargs):
        data = request.data
        errors = {}
        serializer = UserCreateSerializer(data=data)
        is_valid = serializer.is_valid(raise_exception=False)
        msg = ""
        if is_valid:
            self.perform_create(serializer)
            _status = status.HTTP_201_CREATED
            msg = "successfully created user"
        else:
            _status = status.HTTP_400_BAD_REQUEST
            errors = serializer.errors
            if (
                errors.get("non_field_errors")
                and len(errors.get("non_field_errors")) > 0
            ):
                if PASSWORD_NOT_MATCH in errors.get("non_field_errors")[0].__str__():
                    errors["confirm_password"] = errors.get("non_field_errors")
            msg = "Validation Error"
        return Response(
            {
                "status": _status,
                "data": serializer.data,
                "errors": errors,
                "message": msg,
                "msg": msg,
            },
            status=_status,
        )

    def update(self, request, *args, **kwargs):
        errors = {}
        msg = ""
        instance = self.get_object()
        serializer = UserEditSerializer(instance, data=request.data)
        is_valid = serializer.is_valid(raise_exception=False)
        if is_valid:
            self.perform_update(serializer)
            if request.data.get("profile_image") == "null":
                serializer.instance.profile_picture = None
                serializer.instance.thumbnail = None
                serializer.instance.save()
            else:
                serializer.instance.create_thumbnail()
            _status = status.HTTP_201_CREATED
            msg = "successfully updated user"
        else:
            _status = status.HTTP_400_BAD_REQUEST
            errors = serializer.errors

        return Response(
            {
                "status": _status,
                "data": serializer.data,
                "errors": errors,
                "message": msg,
            },
            status=_status,
        )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        product_id = instance.id
        self.perform_destroy(instance)
        return Response(
            {"status": status.HTTP_204_NO_CONTENT, "data": {"id": product_id}},
            status=status.HTTP_200_OK,
        )


class GroupViewSets(ModelViewSet):
    """Base User ViewSet"""

    queryset = Group.objects.filter(profile__is_active=True)
    serializer_class = GroupSerializer
    permission_classes = [AccountPermission]
    filterset_fields = ("name", "id")
    filterset_class = GroupFilter
    search_fields = (
        "id",
        "name",
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(count=Count("id"))
        return queryset

    def get_authenticators(self):
        if not settings.IS_PROD:
            return [CsrfExemptSessionAuthentication()]
        return super().get_authenticators()

    def clean_request_data(self, raw_data):
        return raw_data

    def create(self, request, *args, **kwargs):
        raw_data = request.data
        data = self.clean_request_data(raw_data)
        errors = {}
        serializer = self.serializer_class(data=data)
        is_valid = serializer.is_valid(raise_exception=False)
        msg = ""
        if is_valid:
            self.perform_create(serializer)
            _status = status.HTTP_201_CREATED
            msg = "successfully created user"
        else:
            _status = status.HTTP_400_BAD_REQUEST
            errors = serializer.errors
            if (
                errors.get("non_field_errors")
                and len(errors.get("non_field_errors")) > 0
            ):
                msg = "Validation error"
        return Response(
            {
                "status": _status,
                # "data": serializer.data,
                "errors": errors,
                "message": msg,
                "msg": msg,
            },
            status=_status,
        )

    def update(self, request, *args, **kwargs):
        errors = {}
        msg = ""
        instance = self.get_object()
        raw_data = request.data
        data = self.clean_request_data(raw_data)
        serializer = self.serializer_class(instance, data=data)
        is_valid = serializer.is_valid(raise_exception=False)
        if is_valid:
            self.perform_update(serializer)
            if request.data.get("profile_image"):
                serializer.instance.profile_picture = request.data.get("profile_image")
                serializer.instance.save()
            _status = status.HTTP_201_CREATED
            msg = "successfully updated user"
        else:
            _status = status.HTTP_400_BAD_REQUEST
            errors = serializer.errors
        return Response(
            {
                "status": _status,
                "errors": errors,
                "message": msg,
            },
            status=_status,
        )

    def perform_destroy(self, instance):
        if hasattr(instance, "profile"):
            instance.profile.is_active = False
            instance.profile.save()
        else:
            instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        product_id = instance.id
        self.perform_destroy(instance)
        return Response(
            {"status": status.HTTP_204_NO_CONTENT, "data": {"id": product_id}},
            status=status.HTTP_200_OK,
        )


class PermissionViewSets(ModelViewSet):

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [AccountPermission]
    filterset_fields = ("name", "id", "codename")

    def get_authenticators(self):
        if not settings.IS_PROD:
            return [CsrfExemptSessionAuthentication()]
        return super().get_authenticators()


class UserProfileViewSets(ModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [AccountPermission]
    filterset_class = UserFilter

    def get_authenticators(self):
        if not settings.IS_PROD:
            return [CsrfExemptSessionAuthentication()]
        return super().get_authenticators()

    def get_queryset(self):
        return super().get_queryset()


class UserGroupViewSets(ModelViewSet):

    queryset = Group.objects.all()
    serializer_class = UserGroupSerializer
    permission_classes = [AccountPermission]
    filterset_class = GroupFilter

    def get_authenticators(self):
        if not settings.IS_PROD:
            return [CsrfExemptSessionAuthentication()]
        return super().get_authenticators()

    def get_queryset(self):
        return super().get_queryset()
