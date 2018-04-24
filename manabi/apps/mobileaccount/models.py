from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class MobileSignupRecord(models.Model):
    '''Records that this user signed up from the mobile app.'''
    user = models.OneToOneField(
            User, models.CASCADE, related_name='mobile_signup_record')

