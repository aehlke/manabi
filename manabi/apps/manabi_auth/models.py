import random
import string

from django.contrib.auth.models import User
from django.db import models
from django.db.models.deletion import CASCADE


class AppleIDAccount(models.Model):
    user = models.OneToOneField(User, on_delete=CASCADE)
    user_identifier = models.CharField(
        blank=False,
        unique=True,
        max_length=200,
    )


def generate_username_for_apple_id(first_name, suffix=None):
    username = first_name

    if suffix is not None:
        username = username + suffix

    try:
        User.objects.get(username=username)
        suffix = ''.join(random.choices(string.digits), k=6)
        return generate_username_for_apple_id(first_name, suffix=suffix)
    except User.DoesNotExist:
        return username
