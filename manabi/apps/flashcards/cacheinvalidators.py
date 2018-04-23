from cachecow.cache import invalidate_namespace
from django.db.models.signals import (
    post_save,
    m2m_changed,
    post_delete,
    pre_delete,
)
from django.dispatch import receiver

from cachenamespaces import deck_review_stats_namespace, fact_grid_namespace
from manabi.apps.flashcards.models import Card
from manabi.apps.flashcards.signals import (
    fact_grid_updated,
    post_card_reviewed,
    card_active_field_changed,
)
from .models.fields import FieldContent


@receiver(fact_grid_updated, dispatch_uid='nuke_fact_grid_namespace')
def nuke_fact_grid_namespace(sender, decks=[], **kwargs):
    for deck in decks:
        invalidate_namespace(fact_grid_namespace(deck.pk))



###############################################################################


@receiver(post_save, sender=FieldContent, dispatch_uid='human_readable_field_ps')
def nuke_human_readable_field(sender, instance, created, **kwargs):
    instance.human_readable_content.delete_cache(instance)


###############################################################################


@receiver(post_card_reviewed, dispatch_uid='deck_review_stats_cr')
@receiver(card_active_field_changed, dispatch_uid='deck_review_stats_cafc')
@receiver(pre_delete, sender=Card, dispatch_uid='deck_review_stats_cpd')
def nuke_deck_review_stats_namespace(sender, instance, **kwargs):
    invalidate_namespace(deck_review_stats_namespace(instance.deck_id))
