from adminsortable.models import SortableMixin
from django.db import models


class FeaturedDeck(SortableMixin, models.Model):
    deck = models.OneToOneField('flashcards.Deck')
    ordinal = models.PositiveIntegerField(
        default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['ordinal']

    def __unicode__(self):
        return self.deck.name


def get_featured_decks():
    return [
        feature.deck for feature
        in FeaturedDeck.objects.all().select_related('owner')
        if feature.deck.active and feature.deck.shared
    ]
