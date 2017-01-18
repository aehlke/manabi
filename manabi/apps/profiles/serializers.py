from django.contrib.auth.models import User
from rest_framework import serializers

from manabi.api.serializers import ManabiModelSerializer
from manabi.apps.flashcards.serializers import SharedDeckSerializer


class UserProfileSerializer(ManabiModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'date_joined',
        )
