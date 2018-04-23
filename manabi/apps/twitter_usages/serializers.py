from manabi.api.serializers import ManabiModelSerializer
from manabi.apps.twitter_usages.models import (
    ExpressionTweet,
)


class TweetSerializer(ManabiModelSerializer):
    class Meta:
        model = ExpressionTweet
        fields = (
            'id',
            'tweet',
        )
        read_only_fields = (
            'id',
            'tweet',
        )
