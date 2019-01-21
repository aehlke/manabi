import django.dispatch
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_delete
from manabi.apps.flashcards.models import Card


########################################################################

total_count_changed = django.dispatch.Signal(providing_args=['decks'])


########################################################################

new_count_changed = django.dispatch.Signal(providing_args=['instance'])

@receiver(post_save, sender=Card, dispatch_uid='new_count_changed_cs')
def card_created(sender, instance, created, **kwargs):
    if created and instance.active and not instance.suspended:
        new_count_changed.send(sender=sender, instance=instance)

########################################################################
# Card signals

pre_card_reviewed = django.dispatch.Signal(providing_args=['instance'])
post_card_reviewed = django.dispatch.Signal(providing_args=['instance'])

# When a card's `active` field changes.
# DEPRECATED.
card_active_field_changed = django.dispatch.Signal(providing_args=['instance'])

