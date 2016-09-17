# -*- coding: utf-8 -*-

from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
import pytz

from manabi.api.viewsets import MultiSerializerViewSetMixin
from manabi.apps.flashcards.models import (
    Deck,
    Fact,
    Card,
    ReviewAvailabilities,
    NextCardsForReview,
)
from manabi.apps.flashcards.api_filters import (
    review_availabilities_filters,
    next_cards_to_review_filters,
)
from manabi.apps.flashcards.permissions import (
    DeckSynchronizationPermission,
)
from manabi.apps.flashcards.serializers import (
    CardReviewSerializer,
    CardSerializer,
    DeckSerializer,
    DetailedFactSerializer,
    FactSerializer,
    FactWithCardsSerializer,
    NextCardsForReviewSerializer,
    ReviewAvailabilitiesSerializer,
    SharedDeckSerializer,
    SynchronizedDeckSerializer,
)


class DeckViewSet(viewsets.ModelViewSet):
    serializer_class = DeckSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated():
            return Deck.objects.none()
        return Deck.objects.filter(owner=user, active=True).order_by('name')

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.active = False
        instance.save()

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
        facts = facts.prefetch_related('card_set')
        return Response(DetailedFactSerializer(facts, many=True).data)


class SynchronizedDeckViewSet(viewsets.ModelViewSet):
    serializer_class = SynchronizedDeckSerializer

    permission_classes = [
        IsAuthenticated,
        DeckSynchronizationPermission,
    ]

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return Deck.objects.none()
        return Deck.objects.synchronized_decks(self.request.user)

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)


class SharedDeckViewSet(viewsets.ModelViewSet):
    serializer_class = SharedDeckSerializer

    @detail_route()
    def facts(self, request, pk=None):
        deck = self.get_object()
        facts = Fact.objects.deck_facts(deck)
        return Response(FactSerializer(facts, many=True).data)

    def get_queryset(self):
        decks = Deck.objects.filter(active=True, shared=True)

        if self.request.user.is_authenticated():
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
    }
    permissions_classes = [IsAuthenticated]

    def get_queryset(self):
        facts = Fact.objects.filter(deck__owner=self.request.user)
        facts = facts.filter(active=True).distinct()
        facts = facts.select_related('deck')
        facts = facts.prefetch_related('card_set')
        return facts

    # TODO Special code for getting a specific object, for speed.


class ReviewAvailabilitiesViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _test_helper_get(self, request, format=None):
        from manabi.apps.flashcards.test_stubs import NEXT_CARDS_TO_REVIEW_STUBS
        interstitial = NEXT_CARDS_TO_REVIEW_STUBS[1]['interstitial']
        interstitial['primary_prompt'] = "You'll soon forget 19 expressions—now's a good time to review them."
        interstitial['secondary_prompt'] = "We have 7 more you might have forgotten, plus new ones to learn."

        return Response(interstitial)

    def list(self, request, format=None):
        if settings.USE_TEST_STUBS:
            return self._test_helper_get(request, format=format)

        time_zone = pytz.timezone(
            self.request.META.get('HTTP_X_TIME_ZONE', 'New York'))

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
            self.request.META.get('HTTP_X_TIME_ZONE', 'New York'))

        next_cards_for_review = NextCardsForReview(
            self.request.user,
            5, # FIXME
            excluded_card_ids=excluded_card_ids,
            time_zone=time_zone,
            **next_cards_to_review_filters(self.request)
        )

        serializer = NextCardsForReviewSerializer(
            next_cards_for_review)

        return Response(serializer.data)


class CardViewSet(viewsets.ModelViewSet):
    serializer_class = CardSerializer

    def get_queryset(self):
        return Card.objects.of_user(self.request.user)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def reviews(self, request, pk=None):
        card = self.get_object()
        serializer = CardReviewSerializer(data=request.data)
        if serializer.is_valid():
            card.review(serializer.data['grade'])
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
