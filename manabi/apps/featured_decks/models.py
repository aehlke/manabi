from adminsortable.models import SortableMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q

from manabi.apps.flashcards.models import Deck, DeckCollection
from manabi.apps.flashcards.models.deck_trees import (
    DeckCollectionTreeItem,
    DeckTreeItem,
)


# TODO: Rename to FeaturedDeckTreeItem?
class FeaturedDeck(SortableMixin, models.Model):
    item_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=(
            Q(app_label='flashcards', model='deckcollection')
            | Q(app_label='flashcards', model='deck')
        )
    )
    item_id = models.PositiveIntegerField()
    item = GenericForeignKey('item_content_type', 'item_id')

    ordinal = models.PositiveIntegerField(
        default=0, editable=False, db_index=True)

    # DEPRECATED.
    deck = models.OneToOneField('flashcards.Deck', blank=True, null=True)

    class Meta:
        ordering = ['ordinal']

    def __unicode__(self):
        return self.featured_item.name


def get_featured_decks_tree():
    '''
    Returns a list of `TreeItem` instances.

    Expensive; please wrap with cache.
    '''
    items = [
        featured_deck.item for featured_deck in
        FeaturedDeck.objects.all()
        .prefetch_related('item')
        .order_by('ordinal')
    ]
    tree = []
    for item in items:
        if isinstance(item, DeckCollection):
            tree.append(DeckCollectionTreeItem(item))
        elif isinstance(item, Deck):
            if not (item.active and item.shared):
                continue
            tree.append(DeckTreeItem(item))
        else:
            raise ValueError("Unexpected item type.")
    return tree


# DEPRECATED.
def get_featured_decks():
    return Deck.objects.filter(
        id__in=FeaturedDeck.objects.all().values('deck_id'),
        active=True,
        shared=True,
        deck__isnull=False,
    ).order_by('featureddeck__ordinal')
