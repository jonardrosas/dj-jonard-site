import os
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings


from django.utils.http import urlsafe_base64_decode
from PIL import Image


def generate_reset_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_link = f"{settings.PASSWORD_RESET_LINK}/{uid}/{token}/"
    return reset_link


def decode_uid(uidb64):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        return uid
    except (TypeError, ValueError, OverflowError):
        return None


def is_token_valid(user, token):
    return default_token_generator.check_token(user, token)


def create_thumbnail(
    orig_image, source_image, model_instance, path, width=40, height=40
):
    try:
        if not orig_image:
            return

        thumbnail_size = (width, height)
        img = Image.open(orig_image.path)
        img.thumbnail(thumbnail_size)
        thumb_filename = os.path.split(orig_image.name)[1]
        thumb_dir = os.path.join(settings.MEDIA_ROOT, path)
        if not os.path.exists(thumb_dir):
            os.makedirs(thumb_dir)

        thumb_path = os.path.join(thumb_dir, thumb_filename)
        img.save(thumb_path)

        setattr(model_instance, source_image, os.path.join(path, thumb_filename))
        model_instance.save(update_fields=["thumbnail"])
    except Exception as e:
        if orig_image.url:
            url = orig_image.url.split("media/")[-1]
            setattr(model_instance, source_image, url)
            model_instance.save(update_fields=["thumbnail"])

