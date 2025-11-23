from django.forms import (
    ModelForm,
    ValidationError,
    CharField,
    EmailField,
    PasswordInput,
    Form,
)
from .models import User


class LoginForm(Form):
    username = CharField(max_length=150)
    password = CharField(widget=PasswordInput)


class SignUpForm(ModelForm):
    password = CharField(widget=PasswordInput)
    password_confirm = CharField(widget=PasswordInput, label="Confirm Password")
    email = EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords don't match")
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
