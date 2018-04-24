from catnap.rest_views import ListView, DetailView, DeletionMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404
import catnap.permissions

from manabi.apps.flashcards import models
from manabi.apps.flashcards.models import Card
from manabi.apps.flashcards.models import undo
from manabi.apps.flashcards.restresources import (
    UserResource,
    DeckResource,
    CardResource,
    FactResource,
)
from manabi.apps.utils import japanese, query_cleaner
from manabi.apps.utils.query_cleaner import clean_query
from manabi.apps.utils.shortcuts import get_deck_or_404
from manabi.rest import ManabiRestView


class CardQueryMixin:
    def get_deck(self):
        if (
            'deck' not in self.request.GET and
            'deck' not in self.request.POST and
            'deck' not in self.kwargs
        ):
            return

        deck_id = (
            self.kwargs.get('deck') or
            self.request.GET.get('deck') or
            self.request.POST.get('deck'))
        deck = get_object_or_404(models.Deck, pk=deck_id)

        if not deck.shared and deck.owner.id != self.request.user.id:
            raise PermissionDenied('You do not own this deck.')

        return deck

    def get_card(self):
        if (
            'card' not in self.request.GET and
            'card' not in self.request.POST and
            'card' not in self.kwargs
        ):
            return

        card_id = (
            self.kwargs.get('card') or
            self.request.GET.get('card') or
            self.request.POST.get('card'))
        card = get_object_or_404(models.Card, pk=card_id)

        if card.owner.id != self.request.user.id:
            raise PermissionDenied('You do not own this flashcard.')

        return card


class Decks(ListView, ManabiRestView):
    '''
    List of the logged-in user's decks, including suspended ones.
    '''
    resource_class = DeckResource
    context_object_name = 'decks'
    permissions = catnap.permissions.IsAuthenticated()

    def get_queryset(self):
        return models.Deck.objects.filter(owner=self.request.user, active=True).order_by('name')

    def get_url(self):
        return reverse('api_decks')


class SharedDecks(ListView, ManabiRestView):
    '''
    List of decks people have shared.
    '''
    resource_class = DeckResource
    context_object_name = 'decks'

    def get_queryset(self):
        decks = models.Deck.objects.filter(active=True, shared=True)

        if self.request.user.is_authenticated():
            decks = decks.exclude(owner=self.request.user)

        return decks.order_by('name')

    def get_url(self):
        return reverse('api_shared_decks')


class DeckFacts(CardQueryMixin, ListView, ManabiRestView):
    '''
    List of facts in a deck.
    '''
    resource_class = FactResource
    context_object_name = 'facts'

    def get_queryset(self):
        deck = self.get_deck()
        facts = models.Fact.objects.deck_facts(deck)
        return facts


class DeckCards(CardQueryMixin, ListView, ManabiRestView):
    '''
    List of cards in a deck.
    '''
    resource_class = CardResource
    context_object_name = 'cards'

    def get_queryset(self):
        deck = self.get_deck()
        cards = models.Card.objects.of_deck(deck)
        return cards


class NextCardsForReview(CardQueryMixin, ManabiRestView):
    '''
    Returns a list of Card resources -- the next cards up for review.
    Accepts some query parameters for filtering and influencing what
    cards will be selected.
    '''
    permissions = catnap.permissions.IsAuthenticated()

    query_structure = {
        'count': int,
        'early_review': bool,
        'learn_more': bool,
        'session_start': bool,  # Beginning of review session?
        'excluded_cards': query_cleaner.int_list,
    }

    def get(self, request, **kwargs):
        params = clean_query(request.GET, self.query_structure)

        count = params.get('count', 5)

        next_cards = models.Card.objects.next_cards(
            request.user,
            count,
            excluded_ids=params.get('excluded_cards', []),
            session_start=params.get('session_start'),
            deck=self.get_deck(),
            early_review=params.get('early_review'),
            learn_more=params.get('learn_more'),
        )

        #FIXME need to account for 0 cards returned

        # Assemble a list of the cards to be serialized.
        return self.render_to_response({
            'cards': [CardResource(card).get_data() for card in next_cards],
        })


class Card(CardQueryMixin, DetailView, ManabiRestView):
    def get_object(self):
        return self.get_card()


class CardReview(CardQueryMixin, ManabiRestView):
    permissions = catnap.permissions.IsAuthenticated()

    def get_object(self):
        return self.get_card()

    def post(self, request, **kwargs):
        # `duration` is in seconds (the time taken from viewing the card
        # to clicking Show Answer).
        params = clean_query(request.POST, {
            'grade': int,
            'duration': float,
            'question_duration': float,
        })

        card = self.get_object()

        card.review(params['grade'],
                    duration=params.get('duration'),
                    question_duration=params.get('question_duration'))

        return self.responses.no_content()
