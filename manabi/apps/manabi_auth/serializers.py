from django.contrib.auth.models import User
from djoser.serializers import UserRegistrationSerializer
from rest_framework import authtoken, serializers

from manabi.api.serializers import ManabiModelSerializer


class UserSerializer(ManabiModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'date_joined',
        )


class UserRegistrationWithTokenSerializer(UserRegistrationSerializer):
    auth_token = serializers.SerializerMethodField()

    class Meta(UserRegistrationSerializer.Meta):
        fields = UserRegistrationSerializer.Meta.fields + (
            'auth_token',
        )
        read_only_fields = (
            'auth_token',
        )

    def get_auth_token(self, obj):
        user = obj
        token, _ = authtoken.models.Token.objects.get_or_create(user=user)
        return token.key
