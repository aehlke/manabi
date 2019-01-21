from cachecow.cache import invalidate_namespace
from django.db.models.signals import (
    post_save,
    m2m_changed,
    post_delete,
    pre_delete,
)
from django.dispatch import receiver

from manabi.apps.flashcards.models import Card
from manabi.apps.flashcards.signals import (
    post_card_reviewed,
    card_active_field_changed,
)
from .models.fields import FieldContent


###############################################################################


@receiver(
    post_save, sender=FieldContent,
    dispatch_uid='human_readable_field_ps',
)
def nuke_human_readable_field(sender, instance, created, **kwargs):
    instance.human_readable_content.delete_cache(instance)
