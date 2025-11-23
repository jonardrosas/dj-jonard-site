"""
Account Notification
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from core.helper import generate_reset_link


def send_password_reset_email(user):
    """
    Function that sends email when user request for reset passwrod
    """
    reset_link = generate_reset_link(user)
    subject = "Password Reset Requested"
    message = render_to_string(
        "accounts/password_reset_email.html",
        {
            "user": user,
            "reset_link": reset_link,
        },
    )
    send_mail(subject, message, "", [user.email])
