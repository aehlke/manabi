from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework import generics

from manabi.apps.flashcards.models import Fact
from manabi.apps.twitter_usages.models import (
    ExpressionTweet,
    search_expressions,
)
from manabi.apps.twitter_usages.serializers import (
    TweetSerializer,
)


class TweetsForFactView(generics.ListAPIView):
    serializer_class = TweetSerializer

    MAX_COUNT = 10

    def get_queryset(self):
        fact = get_object_or_404(
            Fact.objects.select_related('deck'), id=self.kwargs['fact_id'])

        # TODO: Use DRF permissions.
        if fact.deck.owner_id != self.request.user.id:
            raise PermissionDenied('You do not own this fact.')

        tweets = ExpressionTweet.objects.filter(
            search_expression__in = search_expressions(fact),
        )
        tweets = tweets.order_by('-average_word_frequency')
        return tweets[:self.MAX_COUNT]
