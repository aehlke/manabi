import logging
from datetime import datetime

from django.shortcuts import get_object_or_404
from rest_framework import serializers

from manabi.api.serializers import (
    ManabiModelSerializer,
    FilterRelatedMixin,
)
from manabi.apps.flashcards.models import (
    Card,
    Deck,
    DeckCollection,
    Fact,
)
from manabi.apps.flashcards.models.constants import ALL_GRADES
from manabi.apps.flashcards.serializer_fields import (
    ViewerSynchronizedDeckField,
)
from manabi.apps.manabi_auth.serializers import UserSerializer
from manabi.apps.reader_sources.serializers import ReaderSourceSerializer


class _BaseDeckSerializer(ManabiModelSerializer):
    owner = UserSerializer(read_only=True)
    original_author = UserSerializer(read_only=True)
    subscriber_count = serializers.SerializerMethodField()

    class Meta(object):
        model = Deck
        fields = (
            'id',
            'owner',
            'original_author',
            'shared_at',
            'created_at',
            'modified_at',
            'name',
            'slug',
            'image_url',
            'description',
            'subscriber_count',
            'card_count',
            'shared',
            'share_url',
            'suspended',
            'is_synchronized',
            'synchronized_with',
        )
        read_only_fields = (
            'id',
            'owner',
            'original_author',
            'slug',
            'image_url',
            'shared_at',
            'share_url',
            'subscriber_count',
            'card_count',
            'is_synchronized',
            'synchronized_with',
            'created_at',
            'modified_at',
        )

    def get_subscriber_count(self, obj):
        try:
            return self.context['subscriber_counts'][obj.id]
        except KeyError:
            return obj.subscriber_count()


class SharedDeckSerializer(_BaseDeckSerializer):
    viewer_synchronized_deck = ViewerSynchronizedDeckField(read_only=True)

    class Meta(object):
        model = Deck
        read_only_fields = fields = (
            'id',
            'owner',
            'name',
            'slug',
            'image_url',
            'description',
            'viewer_synchronized_deck',
            'subscriber_count',
            'card_count',
            'created_at',
            'modified_at',
            'share_url',
        )


class DeckSerializer(_BaseDeckSerializer):
    synchronized_with = SharedDeckSerializer(read_only=True)

    def update(self, instance, validated_data):
        shared = validated_data.pop('shared', None)

        deck = super(DeckSerializer, self).update(instance, validated_data)

        if shared is not None and shared != deck.shared:
            if shared:
                deck.share()
            else:
                deck.unshare()

        return deck


class SynchronizedDeckSerializer(ManabiModelSerializer):
    owner = UserSerializer(read_only=True)
    synchronized_with = serializers.PrimaryKeyRelatedField(
        queryset=Deck.objects.shared_decks()
    )

    class Meta:
        model = Deck
        fields = (
            'id',
            'owner',
            'synchronized_with',
        )
        read_only_fields = (
            'id',
            'owner',
        )

    def create(self, validated_data):
        upstream_deck = validated_data['synchronized_with']
        new_deck = upstream_deck.subscribe(validated_data['owner'])
        return new_deck


class DeckCollectionSerializer(ManabiModelSerializer):
    class Meta:
        model = DeckCollection
        fields = (
            'id',
            'name',
            'image_url',
            'description',
            'created_at',
            'modified_at',
        )
        read_only_fields = fields


class SharedDeckTreeItemSerializer(serializers.Serializer):
    '''
    Trees are two levels deep at most: decks, and collections of decks.

    Tree items contain either a deck, or a deck collection.
    '''
    deck_collection = DeckCollectionSerializer()
    deck = SharedDeckSerializer()


class SuggestedSharedDecksSerializer(serializers.Serializer):
    featured_decks_tree = SharedDeckTreeItemSerializer(many=True)
    latest_shared_decks = SharedDeckSerializer(many=True)

    # DEPRECATED.
    featured_decks = SharedDeckSerializer(many=True)


class FactSerializer(ManabiModelSerializer):
    card_count = serializers.ReadOnlyField()
    suspended = serializers.BooleanField()

    class Meta:
        model = Fact
        fields = (
            'id',
            'active',
            'card_count',
            'created_at',
            'modified_at',

            'deck',
            'suspended',
            'expression',
            'reading',
            'meaning',
        )
        read_only_fields = (
            'id',
            'active',
            'card_count',
            'created_at',
            'modified_at',
        )

    def update(self, instance, validated_data):
        deck = validated_data.pop('deck', None)
        if deck is not None and deck.id != instance.deck_id:
            instance.move_to_deck(deck)

        suspended = validated_data.pop('suspended', None)

        instance.modified_at = datetime.utcnow()
        fact = super(FactSerializer, self).update(instance, validated_data)

        if suspended is not None and suspended != fact.suspended:
            if suspended:
                fact.suspend()
            else:
                fact.unsuspend()

        return fact


class FactWithCardsSerializer(FilterRelatedMixin, FactSerializer):
    card_count = serializers.SerializerMethodField()
    active_card_templates = serializers.MultipleChoiceField(
        choices=[
            ('recognition', 'Recognition'),
            ('production', 'Production'),
            ('kanji_reading', 'Kanji reading'),
            ('kanji_writing', 'Kanji writing'),
        ],
        allow_empty=True,
    )

    class Meta(FactSerializer.Meta):
        fields = FactSerializer.Meta.fields + (
            'active_card_templates',
        )

    def get_card_count(self, obj):
        return len(obj.active_card_templates)

    def filter_deck(self, queryset):
        try:
            user = self.context['request'].user
        except KeyError:
            return queryset
        return queryset.of_user(user)

    def create(self, validated_data):
        active_card_templates = validated_data.pop('active_card_templates')
        fact = super(FactWithCardsSerializer, self).create(validated_data)
        fact.set_active_card_templates(active_card_templates)
        return fact

    def update(self, instance, validated_data):
        active_card_templates = validated_data.pop('active_card_templates', None)

        fact = super(FactWithCardsSerializer, self).update(instance, validated_data)

        if active_card_templates is not None:
            fact.set_active_card_templates(active_card_templates)

        return fact


class ManabiReaderFactWithCardsSerializer(FactWithCardsSerializer):
    reader_source = ReaderSourceSerializer(required=False)

    class Meta:
        model = Fact
        fields = (
            'id',
            'deck',
            'expression',
            'reading',
            'meaning',
            'example_sentence',
            'reader_source',
            'active_card_templates',
        )
        read_only_fields = (
            'id',
            'deck',
        )

    def create(self, validated_data):
        data = validated_data.copy()
        data['deck'] = Deck.objects.get_or_create_manabi_reader_deck(
            self.context['request'].user)
        data['suspended'] = False
        fact = super(ManabiReaderFactWithCardsSerializer, self).create(data)
        return fact


class DetailedFactSerializer(FactWithCardsSerializer):
    deck = serializers.SerializerMethodField()

    def get_deck(self, obj):
        try:
            return self.context['deck_data']
        except KeyError:
            return DeckSerializer(obj.deck).data


class CardSerializer(ManabiModelSerializer):
    expression = serializers.CharField(source='fact.expression')
    reading = serializers.CharField(source='fact.reading')
    meaning = serializers.CharField(source='fact.meaning')

    class Meta(object):
        model = Card

        fields = read_only_fields = (
            'id',
            'deck',
            'fact',
            'ease_factor',
            'interval',
            'due_at',
            'last_ease_factor',
            'last_interval',
            'last_due_at',
            'review_count',
            'template',
            'expression',
            'reading',
            'meaning',
            'is_new',
        )


class DetailedCardSerializer(CardSerializer):
    deck = DeckSerializer()
    suspended = serializers.BooleanField()


class DetailedDeckSerializer(DeckSerializer):
    facts = FactWithCardsSerializer(
        source='facts.prefetch_active_card_templates',
        many=True,
        read_only=True,
    )

    class Meta(DeckSerializer.Meta):
        fields = DeckSerializer.Meta.fields + (
            'facts',
        )


class DetailedSharedDeckSerializer(SharedDeckSerializer):
    facts = FactWithCardsSerializer(
        source='facts.prefetch_active_card_templates',
        many=True,
        read_only=True,
    )

    class Meta(DeckSerializer.Meta):
        fields = DeckSerializer.Meta.fields + (
            'facts',
        )


class ReviewAvailabilitiesSerializer(serializers.Serializer):
    ready_for_review = serializers.BooleanField()
    early_review_available = serializers.BooleanField()

    next_new_cards_count = serializers.IntegerField()
    buried_new_cards_count = serializers.IntegerField()
    new_cards_per_day_limit_reached = serializers.BooleanField()
    new_cards_per_day_limit_override = serializers.IntegerField()

    invalidated_upon_card_failure = serializers.BooleanField()

    primary_prompt = serializers.CharField()
    secondary_prompt = serializers.CharField()

    trial_prompt = serializers.CharField()

    class Meta:
        read_only_fields = (
            'ready_for_review',
            'next_new_cards_count',
            'buried_new_cards_count',
            'early_review_available',
        )


class ReviewInterstitialSerializer(serializers.Serializer):
    review_availabilities = ReviewAvailabilitiesSerializer(required=True)

    class Meta:
        read_only_fields = (
            'review_availabilities',
        )


class NextCardsForReviewSerializer(serializers.Serializer):
    cards = CardSerializer(many=True)

    # `None` means it should not display an interstitial, and should continue
    # requesting the next cards for review.
    interstitial = ReviewInterstitialSerializer(required=False)

    server_datetime = serializers.DateTimeField()

    class Meta:
        read_only_fields = (
            'cards',
            'interstitial',
        )


class CardReviewSerializer(serializers.Serializer):
    grade = serializers.ChoiceField(choices=ALL_GRADES)

    next_due_at = serializers.DateTimeField(read_only=True)
    humanized_next_due_in = serializers.CharField(read_only=True)
