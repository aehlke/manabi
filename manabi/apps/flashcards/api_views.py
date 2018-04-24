# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework_extensions.cache.mixins import cache_response
import pytz

from manabi.api.viewsets import MultiSerializerViewSetMixin
from manabi.apps.featured_decks.models import (
    get_featured_decks_tree,
    get_featured_decks,
)
from manabi.apps.flashcards.models import (
    DeckCollection,
    Deck,
    Fact,
    Card,
    ReviewAvailabilities,
    NextCardsForReview,
    UndoCardReview,
)
from manabi.apps.flashcards.models.trial_limits import (
    cards_remaining_in_daily_trial,
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
    DeckCollectionSerializer,
    DeckSerializer,
    DetailedFactSerializer,
    FactSerializer,
    FactWithCardsSerializer,
    ManabiReaderFactWithCardsSerializer,
    NextCardsForReviewSerializer,
    ReviewAvailabilitiesSerializer,
    SharedDeckSerializer,
    SuggestedSharedDecksSerializer,
    SynchronizedDeckSerializer,
)
from manabi.apps.manabi_auth.serializers import UserSerializer


class _DeckMixin:
    @detail_route()
    def subscribers(self, request, pk=None):
        deck = self.get_object()
        if not (deck.shared and deck.active):
            raise Http404()
        subscribers = deck.subscribers().order_by('username')
        return Response(UserSerializer(subscribers, many=True).data)


class DeckViewSet(_DeckMixin, viewsets.ModelViewSet):
    serializer_class = DeckSerializer
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return (
            Deck.objects
            .of_user(self.request.user)
            .select_related('owner', 'synchronized_with')
        )

    def get_serializer_context(self):
        context = super(DeckViewSet, self).get_serializer_context()
        queryset = self.filter_queryset(self.get_queryset())
        upstream_queryset = Deck.objects.filter(
            id__in=queryset.filter(synchronized_with__isnull=False).values_list('synchronized_with_id', flat=True),
        )
        queryset_for_counts = queryset | upstream_queryset
        context.update({
            'subscriber_counts': queryset_for_counts.subscriber_counts(),
        })
        return context

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
    http_method_names = ['post']

    permission_classes = [
        IsAuthenticatedOrReadOnly,
        DeckSynchronizationPermission,
    ]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Deck.objects.none()
        return Deck.objects.synchronized_decks(self.request.user)

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)


class SuggestedSharedDecksViewSet(viewsets.ViewSet):
    def list(self, request, format=None):
        featured_decks_tree = get_featured_decks_tree()
        featured_decks = get_featured_decks().select_related('owner')
        latest_decks = (
            Deck.objects.latest_shared_decks().select_related('owner'))

        featured_deck_ids = [
            item.deck.id for item in featured_decks_tree
            if item.deck is not None
        ]

        all_suggested_decks = Deck.objects.filter(
            Q(id__in=featured_deck_ids)
            | Q(id__in=latest_decks.values('id'))
        ).distinct()

        context = {
            'subscriber_counts': all_suggested_decks.subscriber_counts(),
        }

        if self.request.user.is_authenticated:
            context['viewer_synchronized_decks'] = list(
                Deck.objects.synchronized_decks(self.request.user)
                .filter(active=True)
                .select_related('owner', 'synchronized_with__owner')
            )

        serializer = SuggestedSharedDecksSerializer({
            'featured_decks_tree': featured_decks_tree,
            'latest_shared_decks': latest_decks,
            'featured_decks': featured_decks,
        }, context=context)
        return Response(serializer.data)


class SharedDeckViewSet(_DeckMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = SharedDeckSerializer

    @detail_route()
    def facts(self, request, pk=None):
        deck = self.get_object()
        facts = Fact.objects.deck_facts(deck)
        facts = facts.select_related('deck')
        facts = facts.prefetch_active_card_templates()

        return Response(
            FactSerializer(facts, many=True).data
        )

    def get_queryset(self):
        decks = (
            Deck.objects
            .filter(active=True, shared=True)
            .select_related('owner')
        )

        collection_id = self.request.query_params.get('deck_collection_id')
        if collection_id is not None:
            decks = decks.filter(collection_id=collection_id)

        user_id = self.request.query_params.get('user_id')
        if user_id is not None:
            user = get_object_or_404(get_user_model(), id=user_id)
            decks = decks.shared_decks_owned_or_subcribed_by_user(user)
        elif self.request.user.is_authenticated and self.action == 'list':
            decks = decks.exclude(owner=self.request.user)

        return decks.order_by('collection_ordinal', 'name')

    def get_serializer_context(self):
        context = super(SharedDeckViewSet, self).get_serializer_context()
        queryset_for_counts = self.filter_queryset(self.get_queryset())
        if self.request.user.is_authenticated:
            viewer_subscribed_decks = Deck.objects.filter(
                synchronized_with_id__in=queryset_for_counts.values_list(
                    'id', flat=True),
                owner=self.request.user,
            )
            queryset_for_counts |= viewer_subscribed_decks
        context.update({
            'subscriber_counts': queryset_for_counts.subscriber_counts(),
            'viewer_synchronized_decks': list(
                Deck.objects.synchronized_decks(self.request.user)
                .filter(active=True)
                .select_related('owner', 'synchronized_with__owner')
            )
        })
        return context


class FactViewSet(MultiSerializerViewSetMixin, viewsets.ModelViewSet):
    serializer_class = DetailedFactSerializer
    serializer_action_classes = {
        'create': FactWithCardsSerializer,
        'update': FactWithCardsSerializer,
        'partial_update': FactWithCardsSerializer,
    }
    permission_classes = [
        IsAuthenticated,
        IsOwnerPermission,
    ]

    def get_queryset(self):
        if self.request.user.is_anonymous:
            facts = Fact.objects.filter(deck__shared=True)
        else:
            facts = Fact.objects.filter(deck__owner=self.request.user)
        facts = facts.filter(active=True).distinct()
        facts = facts.select_related('deck')
        facts = facts.prefetch_related('card_set')
        return facts

    # TODO Special code for getting a specific object, for speed.


class ManabiReaderFactViewSet(
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    serializer_class = ManabiReaderFactWithCardsSerializer
    permission_classes = [
        IsAuthenticated,
    ]


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

        availabilities = ReviewAvailabilities(
            request.user,
            time_zone=request.user_timezone,
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

        card_limit = 10
        trial_cards_remaining = cards_remaining_in_daily_trial(
            self.request.user,
            time_zone=request.user_timezone,
        )
        if trial_cards_remaining is not None:
            card_limit = min(card_limit, trial_cards_remaining)

        next_cards_for_review = NextCardsForReview(
            self.request.user,
            card_limit,
            excluded_card_ids=excluded_card_ids,
            time_zone=request.user_timezone,
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
    permission_classes = [IsOwnerPermission]

    def get_queryset(self):
        return (
            Card.objects.of_user(self.request.user)
            .select_related('fact', 'deck')
        )

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
