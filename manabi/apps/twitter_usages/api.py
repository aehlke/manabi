from catnap.rest_views import ListView, DetailView, DeletionMixin
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from manabi.apps.flashcards.models import Fact
from manabi.apps.twitter_usages.models import (
    ExpressionTweet,
    search_expressions,
)


class FactTweets(ListView, ManabiRestView):
    '''
    Tweets that correspond to a given fact.
    '''
    resource_class = TweetResource
    context_object_name = 'tweets'

    MAX_COUNT = 10

    def get_queryset(self):
        fact_id = self.kwargs.get('fact')
        fact = get_object_or_404(Fact, pk=fact_id)

        if fact.deck.owner_id != self.request.user.id:
            raise PermissionDenied('You do not own this fact.')

        return ExpressionTweet.objects.filter(
            search_expression__in = search_expressions(fact),
        )[:MAX_COUNT]
