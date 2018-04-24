import datetime
import time

import dateutil.parser
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import (
    models,
    transaction,
)


def _get_model_fields(model_instance, excluded_field_types=['AutoField', 'ForeignKey']):
    field_names = []
    for field in model_instance._meta.fields:
        if field.get_internal_type() in excluded_field_types:
            continue
        field_names.append(field.name)
    return field_names


class UndoCardReviewManager(models.Manager):
    def of_user(self, user):
        undos = self.filter(user=user)
        return undos

    def _last_undo(self, user):
        '''
        Returns the last undo for `user`.
        '''
        try:
            last_undo = self.of_user(user).order_by('timestamp')[0]
        except IndexError:
            return None
        return last_undo

    @transaction.atomic
    def reset(self, user):
        '''
        Clears the Undo stack for `user`.
        '''
        self.of_user(user).delete()

    @transaction.atomic
    def add_undo(self, card_history):
        '''
        Only keeps 1 level undo for now, to simplify things.
        '''
        user = card_history.card.fact.deck.owner

        SKIP_FIELDS = {
            'new_card_ordinal', 'suspended', 'deck', 'fact', 'owner',
            'template',
        }

        snapshot = {
            field_name: getattr(card_history.card, field_name)
            for field_name in _get_model_fields(card_history.card)
            if field_name not in SKIP_FIELDS
        }
        for key, value in snapshot.items():
            # Be sure to update the reverse mapping in `undo`.
            # If this gets unwieldy, find a 3rd-party lib for this.
            if isinstance(value, datetime.timedelta):
                snapshot[key] = value.total_seconds()
            elif isinstance(value, datetime.datetime):
                snapshot[key] = value.isoformat()

        undo = UndoCardReview(
            user=user,
            card=card_history.card,
            card_history=card_history,
            card_snapshot=snapshot,
        )

        # Delete previous undo if it exists.
        for user_undo in self.of_user(user):
            user_undo.delete()

        undo.save()

    @transaction.atomic
    def undo(self, user):
        '''
        Undoes the last review for `user`.

        Returns the undone review's card, or None if there wasn't
        anything in the undo stack.
        '''
        last_undo = self._last_undo(user)
        if not last_undo:
            return

        card = last_undo.card
        card_history = last_undo.card_history

        # Overwrite the card model with its pickled counterpart
        card_fields = _get_model_fields(card)
        for field_name in card_fields:
            try:
                value = last_undo.card_snapshot[field_name]
            except KeyError:
                continue
            field_type = card._meta.get_field(field_name)

            if value is not None:
                if isinstance(field_type, models.DurationField):
                    value = datetime.timedelta(seconds=value)
                elif isinstance(field_type, models.DateTimeField):
                    value = dateutil.parser.parse(value)

            setattr(card, field_name, value)
        card.save(update_fields=card_fields)

        card_history.delete()

        # Delete this undo now that it's done
        last_undo.delete()

        return card


class UndoCardReview(models.Model):
    objects = UndoCardReviewManager()

    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    user = models.ForeignKey(User, models.CASCADE)  # Denormalization optimization
    card = models.ForeignKey('Card', models.CASCADE)
    card_history = models.ForeignKey('CardHistory', models.CASCADE)

    card_snapshot = JSONField()

    class Meta:
        app_label = 'flashcards'
