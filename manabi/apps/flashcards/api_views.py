# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
import pytz

from manabi.api.viewsets import MultiSerializerViewSetMixin
from manabi.apps.featured_decks.models import get_featured_decks
from manabi.apps.flashcards.models import (
    Deck,
    Fact,
    Card,
    ReviewAvailabilities,
    NextCardsForReview,
    UndoCardReview,
)
from manabi.apps.flashcards.api_filters import (
    review_availabilities_filters,
    next_cards_to_review_filters,
)
from manabi.apps.flashcards.models.card_review import (
    CardReview,
)
from manabi.apps.flashcards.permissions import (
    DeckSynchronizationPermission,
    IsOwnerPermission,
)
from manabi.apps.flashcards.serializers import (
    CardReviewSerializer,
    CardSerializer,
    DetailedCardSerializer,
    DeckSerializer,
    DetailedFactSerializer,
    FactSerializer,
    FactWithCardsSerializer,
    NextCardsForReviewSerializer,
    ReviewAvailabilitiesSerializer,
    SharedDeckSerializer,
    SuggestedSharedDecksSerializer,
    SynchronizedDeckSerializer,
)


class DeckViewSet(viewsets.ModelViewSet):
    serializer_class = DeckSerializer
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return (
            Deck.objects
            .of_user(self.request.user)
            .select_related('owner', 'synchronized_with')
        )

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)

    @detail_route()
    def cards(self, request, pk=None):
        deck = self.get_object()
        cards = Card.objects.of_deck(deck)
        return Response(CardSerializer(cards, many=True).data)

    @detail_route()
    def facts(self, request, pk=None):
        deck = self.get_object()
        facts = Fact.objects.deck_facts(deck)
        facts = facts.select_related('deck')
        facts = facts.prefetch_active_card_templates()

        deck_serializer = DeckSerializer(deck)

        serializer = DetailedFactSerializer(
            facts,
            many=True,
            context={
                'deck_data': deck_serializer.data,
            },
        )
        return Response(serializer.data)


class SynchronizedDeckViewSet(viewsets.ModelViewSet):
    serializer_class = SynchronizedDeckSerializer

    permission_classes = [
        IsAuthenticatedOrReadOnly,
        DeckSynchronizationPermission,
    ]

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return Deck.objects.none()
        return Deck.objects.synchronized_decks(self.request.user)

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)


class SuggestedSharedDecksViewSet(viewsets.ViewSet):
    def list(self, request, format=None):
        serializer = SuggestedSharedDecksSerializer({
            'featured_decks': get_featured_decks(),
            'latest_shared_decks': Deck.objects.latest_shared_decks(),
        })
        return Response(serializer.data)


class SharedDeckViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SharedDeckSerializer

    @detail_route()
    def facts(self, request, pk=None):
        deck = self.get_object()
        facts = Fact.objects.deck_facts(deck)
        return Response(FactSerializer(facts, many=True).data)

    def get_queryset(self):
        decks = Deck.objects.filter(active=True, shared=True)

        user_id = self.request.query_params.get('user_id')
        if user_id is not None:
            user = get_object_or_404(get_user_model(), id=user_id)
            decks = decks.shared_decks_owned_or_subcribed_by_user(user)
        elif self.request.user.is_authenticated():
            decks = decks.exclude(owner=self.request.user)

        return decks.order_by('name')

    def get_serializer_context(self):
        context = super(SharedDeckViewSet, self).get_serializer_context()

        context['viewer_synchronized_decks'] = list(
            Deck.objects.synchronized_decks(self.request.user).filter(active=True)
        )

        return context


class FactViewSet(MultiSerializerViewSetMixin, viewsets.ModelViewSet):
    serializer_class = DetailedFactSerializer
    serializer_action_classes = {
        'create': FactWithCardsSerializer,
        'update': FactWithCardsSerializer,
        'partial_update': FactWithCardsSerializer,
    }
    permissions_classes = [
        IsAuthenticated,
        IsOwnerPermission,
    ]

    def get_queryset(self):
        if self.request.user.is_anonymous():
            facts = Fact.objects.filter(deck__shared=True)
        else:
            facts = Fact.objects.filter(deck__owner=self.request.user)
        facts = facts.filter(active=True).distinct()
        facts = facts.select_related('deck')
        facts = facts.prefetch_related('card_set')
        return facts

    # TODO Special code for getting a specific object, for speed.


class ReviewAvailabilitiesViewSet(viewsets.ViewSet):
    def _test_helper_get(self, request, format=None):
        from manabi.apps.flashcards.test_stubs import NEXT_CARDS_TO_REVIEW_STUBS
        interstitial = NEXT_CARDS_TO_REVIEW_STUBS[1]['interstitial']
        interstitial['primary_prompt'] = (
            "You'll soon forget 19 expressions—now's a good time to review them.")
        interstitial['secondary_prompt'] = (
            "We have 7 more you might have forgotten, plus new ones to learn.")

        return Response(interstitial)

    def list(self, request, format=None):
        if settings.USE_TEST_STUBS:
            return self._test_helper_get(request, format=format)

        time_zone = pytz.timezone(
            self.request.META.get('HTTP_X_TIME_ZONE', 'America/New_York'))

        availabilities = ReviewAvailabilities(
            request.user,
            time_zone=time_zone,
            **review_availabilities_filters(self.request)
        )

        serializer = ReviewAvailabilitiesSerializer(
            availabilities)
        return Response(serializer.data)


class NextCardsForReviewViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _test_helper_get(
        self, request,
        format=None,
        excluded_card_ids=set(),
    ):
        import random
        from manabi.apps.flashcards.test_stubs import NEXT_CARDS_TO_REVIEW_STUBS

        STUBS = NEXT_CARDS_TO_REVIEW_STUBS
        if not excluded_card_ids:
            cards_to_review = STUBS[0].copy()
        elif excluded_card_ids == set(c['id'] for c in STUBS[0]['cards']):
            cards_to_review = STUBS[1].copy()
        else:
            cards_to_review = STUBS[2].copy()
        cards_to_review = STUBS[2].copy()

        if cards_to_review['interstitial']:
            if False: #random.choice([True, False, False, False]):
                cards_to_review['interstitial'] = None
            else:
                cards_to_review['interstitial']['more_cards_ready_for_review'] = (
                    random.choice([True, False])
                )
                cards_to_review['interstitial']['primary_prompt'] = (
                    "You'll soon forget 19 expressions—now's a good time to review them.")
                cards_to_review['interstitial']['secondary_prompt'] = (
                    "We have 7 more you might have forgotten, plus new ones to learn.")

        return Response(cards_to_review)

    def _get_excluded_card_ids(self, request):
        try:
            return set(
                int(id_) for id_ in
                request.query_params['excluded_card_ids'].split(',')
            )
        except KeyError:
            return set()
        except TypeError:
            raise ValidationError("Couldn't parse card IDs.")

    def list(self, request, format=None):
        excluded_card_ids = self._get_excluded_card_ids(request)

        if settings.USE_TEST_STUBS:
            return self._test_helper_get(
                request, format=format, excluded_card_ids=excluded_card_ids)

        time_zone = pytz.timezone(
            self.request.META.get('HTTP_X_TIME_ZONE', 'America/New_York'))

        next_cards_for_review = NextCardsForReview(
            self.request.user,
            7, # FIXME
            excluded_card_ids=excluded_card_ids,
            time_zone=time_zone,
            **next_cards_to_review_filters(self.request)
        )

        serializer = NextCardsForReviewSerializer(
            next_cards_for_review)

        return Response(serializer.data)


class CardViewSet(viewsets.ModelViewSet):
    serializer_class = CardSerializer
    serializer_action_classes = {
        'retrieve': DetailedCardSerializer,
    }
    permissions_classes = [IsOwnerPermission]

    def get_queryset(self):
        return Card.objects.of_user(self.request.user)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def reviews(self, request, pk=None):
        card = self.get_object()
        input_serializer = CardReviewSerializer(data=request.data)
        if input_serializer.is_valid():
            card_review = CardReview(card, input_serializer.data['grade'])
            card_review.apply_review()
            output_serializer = CardReviewSerializer(card_review)
            return Response(output_serializer.data)
        else:
            return Response(input_serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class UndoCardReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        card = UndoCardReview.objects.undo(request.user)

        if card is None:
            return Response("Nothing to undo.", status=status.HTTP_404_NOT_FOUND)

        return Response(CardSerializer(card).data)
