from adminsortable.models import SortableMixin
from django.db import models

from manabi.apps.flashcards.models import Deck


class FeaturedDeck(SortableMixin, models.Model):
    deck = models.OneToOneField('flashcards.Deck')
    ordinal = models.PositiveIntegerField(
        default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['ordinal']

    def __unicode__(self):
        return self.deck.name


def get_featured_decks():
    return Deck.objects.filter(
        id__in=FeaturedDeck.objects.all().values('deck_id'),
        active=True,
        shared=True,
    ).order_by('featureddeck__ordinal')
