from adminsortable.models import SortableMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q

from manabi.apps.flashcards.models import Deck, DeckCollection


# TODO: Rename to FeaturedDeckTreeItem?
class FeaturedDeck(SortableMixin, models.Model):
    ordinal = models.PositiveIntegerField(
        default=0, editable=False, db_index=True)

    # Use one or the other, not both.
    deck_collection = models.OneToOneField(
        'flashcards.DeckCollection', models.CASCADE, blank=True, null=True)
    deck = models.OneToOneField(
        'flashcards.Deck', models.CASCADE,
        blank=True, null=True)

    class Meta:
        ordering = ['ordinal']

    def __unicode__(self):
        try:
            return self.deck_collection.name
        except AttributeError:
            try:
                return self.deck.name
            except AttributeError:
                return '(none set)'


def get_featured_decks_tree():
    '''
    Returns a list of `TreeItem` instances.

    Expensive; please wrap with cache.
    '''
    return (
        FeaturedDeck.objects.all()
        .select_related('deck_collection', 'deck')
        .filter(Q(deck__shared=True, deck__active=True) | Q(deck_collection__isnull=False))
        .order_by('ordinal')
        .only('deck_collection', 'deck')
    )


# DEPRECATED.
def get_featured_decks():
    return Deck.objects.filter(
        id__in=FeaturedDeck.objects.filter(deck__isnull=False).values('deck_id'),
        active=True,
        shared=True,
    ).order_by('featureddeck__ordinal')
