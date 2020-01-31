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
    DeckPrimaryKeyRelatedField,
)
from manabi.apps.manabi_auth.serializers import UserSerializer
from manabi.apps.reader_sources.models import ReaderSource
from manabi.apps.reader_sources.serializers import ReaderSourceSerializer


class _BaseDeckSerializer(ManabiModelSerializer):
    owner = UserSerializer(read_only=True)
    original_author = UserSerializer(read_only=True)
    subscriber_count = serializers.SerializerMethodField()

    class Meta:
        model = Deck
        fields = [
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
        ]
        read_only_fields = [
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
        ]

    def get_subscriber_count(self, obj):
        try:
            return self.context['subscriber_counts'][obj.id]
        except KeyError:
            return obj.subscriber_count()


class SharedDeckSerializer(_BaseDeckSerializer):
    viewer_synchronized_deck = ViewerSynchronizedDeckField(read_only=True)

    class Meta:
        model = Deck
        read_only_fields = fields = [
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
        ]


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
        fields = [
            'id',
            'owner',
            'synchronized_with',
        ]
        read_only_fields = [
            'id',
            'owner',
        ]

    def create(self, validated_data):
        upstream_deck = validated_data['synchronized_with']
        new_deck = upstream_deck.subscribe(validated_data['owner'])
        return new_deck


class DeckCollectionSerializer(ManabiModelSerializer):
    class Meta:
        model = DeckCollection
        fields = [
            'id',
            'name',
            'image_url',
            'description',
            'created_at',
            'modified_at',
        ]
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
    reader_source = ReaderSourceSerializer(required=False)
    jmdict_id = serializers.IntegerField(required=False)

    class Meta:
        model = Fact
        fields = [
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
            'reader_source',
            'jmdict_id',
        ]
        read_only_fields = [
            'id',
            'active',
            'card_count',
            'created_at',
            'modified_at',
        ]

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

    def create(self, validated_data):
        reader_source = None
        reader_source_data = validated_data.pop('reader_source', None)
        if reader_source_data is not None:
            (reader_source, _) = ReaderSource.objects.get_or_create(
                source_url=reader_source_data['source_url'],
                defaults={
                    'title': reader_source_data['title'],
                    'thumbnail_url': reader_source_data.get('thumbnail_url'),
                },
            )
            validated_data['reader_source_id'] = reader_source.id

        (fact, _) = Fact.objects.update_or_create(
            deck=validated_data['deck'],
            expression=validated_data['expression'],
            reading=validated_data.get('reading'),
            meaning=validated_data['meaning'],
            jmdict_id=validated_data.get('jmdict_id'),
            defaults=validated_data,
        )
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
        fields = FactSerializer.Meta.fields + [
            'active_card_templates',
        ]

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
        active_card_templates = validated_data.pop(
            'active_card_templates', None)

        fact = super().update(instance, validated_data)

        if active_card_templates is not None:
            fact.set_active_card_templates(active_card_templates)

        return fact


class ManabiReaderFactWithCardsSerializer(FactWithCardsSerializer):
    class Meta:
        model = Fact
        fields = [
            'id',
            'deck',
            'expression',
            'reading',
            'meaning',
            'active_card_templates',
            'example_sentence',
            'reader_source',
            'jmdict_id',
        ]
        read_only_fields = [
            'id',
            'deck',
        ]

    def create(self, validated_data):
        return Fact.objects.update_or_create_for_manabi_reader(
            self.context['request'].user,
            validated_data['expression'],
            validated_data['reading'],
            validated_data['meaning'],
            validated_data['active_card_templates'],
            jmdict_id=validated_data.get('jmdict_id'),
            example_sentence=validated_data.get('example_sentence'),
            reader_source_data=validated_data.get('reader_source'),
        )


class DetailedFactSerializer(FactWithCardsSerializer):
    #  deck = DeckPrimaryKeyRelatedField()
    deck = serializers.SerializerMethodField()

    class Meta(FactSerializer.Meta):
        fields = FactWithCardsSerializer.Meta.fields + [
            'example_sentence',
            'reader_source',
        ]

    def get_deck(self, obj):
        try:
            return self.context['deck_data']
        except KeyError:
            return DeckSerializer(obj.deck).data


class DeckFactSerializer(FactWithCardsSerializer):
    #  deck = DeckPrimaryKeyRelatedField()
    deck = serializers.SerializerMethodField()

    class Meta(FactSerializer.Meta):
        fields = [
            field for field in
            FactWithCardsSerializer.Meta.fields + [
                'example_sentence',
                'reader_source',
            ]
        ]

    def get_deck(self, obj):
        try:
            return self.context['deck_data']
        except KeyError:
            return DeckSerializer(obj.deck).data



class SuspendFactsSerializer(serializers.Serializer):
    reading = serializers.CharField()
    jmdict_id = serializers.IntegerField(required=False)
    fact_ids = serializers.ListField(
        child=serializers.IntegerField(),
        read_only=True,
    )

    def create(self, validated_data):
        user = self.context['request'].user
        suspended_facts = Fact.objects.filter(
            deck__owner=user, active=True,
        ).suspend_matching(
            validated_data['reading'],
            jmdict_id=validated_data.get('jmdict_id'),
        )
        data = validated_data.copy()
        data['fact_ids'] = suspended_facts.values_list('id', flat=True)
        return data


class CardSerializer(ManabiModelSerializer):
    expression = serializers.CharField(source='fact.expression')
    reading = serializers.CharField(source='fact.reading')
    meaning = serializers.CharField(source='fact.meaning')

    example_sentence = serializers.CharField(source='fact.example_sentence')
    reader_source = ReaderSourceSerializer(source='fact.reader_source')

    class Meta:
        model = Card

        fields = read_only_fields = [
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

            'example_sentence',
            'reader_source',
        ]


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
        fields = DeckSerializer.Meta.fields + [
            'facts',
        ]


class DetailedSharedDeckSerializer(SharedDeckSerializer):
    facts = FactWithCardsSerializer(
        source='facts.prefetch_active_card_templates',
        many=True,
        read_only=True,
    )

    class Meta(DeckSerializer.Meta):
        fields = DeckSerializer.Meta.fields + [
            'facts',
        ]


class ReviewAvailabilitiesRequestSerializer(serializers.Serializer):
    jmdict_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )
    words_without_jmdict_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    is_for_manabi_reader = serializers.BooleanField(default=False)


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
    trial_limit_reached = serializers.BooleanField()

    class Meta:
        read_only_fields = [
            'ready_for_review',
            'early_review_available',
            'next_new_cards_count',
            'buried_new_cards_count',
            'new_cards_per_day_limit_reached',
            'new_cards_per_day_limit_override',
            'invalidated_upon_card_failure',
            'primary_prompt',
            'secondary_prompt',
            'trial_prompt',
            'trial_limit_reached',
        ]


class ReviewInterstitialSerializer(serializers.Serializer):
    review_availabilities = ReviewAvailabilitiesSerializer(required=True)

    class Meta:
        read_only_fields = [
            'review_availabilities',
        ]


class NextCardsForReviewRequestSerializer(
    ReviewAvailabilitiesRequestSerializer,
):
    pass


class NextCardsForReviewSerializer(serializers.Serializer):
    cards = CardSerializer(many=True)

    # `None` means it should not display an interstitial, and should continue
    # requesting the next cards for review.
    interstitial = ReviewInterstitialSerializer(required=False)

    server_datetime = serializers.DateTimeField()

    class Meta:
        read_only_fields = [
            'cards',
            'interstitial',
        ]


class CardReviewSerializer(serializers.Serializer):
    grade = serializers.ChoiceField(choices=ALL_GRADES)

    next_due_at = serializers.DateTimeField(read_only=True)
    humanized_next_due_in = serializers.CharField(read_only=True)
