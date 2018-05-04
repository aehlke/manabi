from django.contrib.auth.models import User
from djoser.serializers import UserCreateSerializer
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


class UserCreateWithTokenSerializer(UserCreateSerializer):
    auth_token = serializers.SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):
        fields = UserCreateSerializer.Meta.fields + (
            'auth_token',
        )
        read_only_fields = (
            'auth_token',
        )

    def get_auth_token(self, obj):
        user = obj
        token, _ = authtoken.models.Token.objects.get_or_create(user=user)
        return token.key


class SocialAccessTokenSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token.
    """
    access_token = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )
