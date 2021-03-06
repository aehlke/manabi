from django.shortcuts import get_object_or_404
from rest_framework import serializers

from manabi.apps.flashcards.models import Deck


class ViewerSynchronizedDeckField(serializers.Field):
    def get_attribute(self, obj):
        return obj

    def to_representation(self, obj):
        from manabi.apps.flashcards.serializers import DeckSerializer

        if obj.id is None:
            return None

        try:
            synchronized_decks = self.context['viewer_synchronized_decks']
        except KeyError:
            return None

        try:
            synchronized_deck = next(
                deck for deck in synchronized_decks
                if deck.synchronized_with_id == obj.id
            )
        except StopIteration:
            return None

        return DeckSerializer(
            synchronized_deck,
            context={
                'subscriber_counts': self.context['subscriber_counts'],
            },
        ).data


class DeckPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = Deck.objects.of_user(user)
        return queryset


class DetailedDeckField(serializers.Field):
    def to_representation(self, obj):
        from manabi.apps.flashcards.serializers import DeckSerializer

        try:
            return self.context['deck_data']
        except KeyError:
            return DeckSerializer(obj).data

    def to_internal_value(self, data):
        deck_id = data
        return get_object_or_404(Deck, id=deck_id)
