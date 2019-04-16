from django.db import models
from django.db.models import Case, When, Value, F
from django.utils.functional import cached_property

from manabi.apps.flashcards.models import Fact, Card
from manabi.apps.flashcards.models.constants import (
    MATURE_INTERVAL_MIN,
)


class TrackedWords:
    def __init__(self, user):
        self.user = user
        self._tracked_words = None

    def _get_tracked_words(self):
        '''
        Includes suspended cards (that the user may have already reviewed).
        '''
        if self._tracked_words is None:
            self._tracked_words = Card.objects.filter(
                owner=self.user,
                active=True,
            ).annotate(
                is_new=Case(
                    When(last_reviewed_at__isnull=True, then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                ),
                is_mature=Case(
                    When(interval__gte=MATURE_INTERVAL_MIN, then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                ),
                reading=Case(
                    When(jmdict_id__isnull=True, then=F('fact__reading')),
                    default=Value(None),
                    output_field=models.CharField(),
                ),
            ).distinct().values('jmdict_id', 'reading', 'is_new', 'is_mature')
        return self._tracked_words

    @cached_property
    def new_jmdict_ids(self):
        new_jmdict_ids = set(
            word['jmdict_id'] for word in self._get_tracked_words()
            if (
                word['is_new']
                and word['jmdict_id'] is not None
            )
        )
        new_jmdict_ids -= self.learning_jmdict_ids
        new_jmdict_ids -= self.known_jmdict_ids
        return new_jmdict_ids

    @cached_property
    def learning_jmdict_ids(self):
        learning_jmdict_ids = set(
            word['jmdict_id'] for word in self._get_tracked_words()
            if (
                not word['is_new']
                and not word['is_mature']
                and word['jmdict_id'] is not None
            )
        )
        learning_jmdict_ids -= self.known_jmdict_ids
        return learning_jmdict_ids

    @cached_property
    def known_jmdict_ids(self):
        return set(
            word['jmdict_id'] for word in self._get_tracked_words()
            if (
                word['is_mature']
                and word['jmdict_id'] is not None
            )
        )

    @cached_property
    def new_words_without_jmdict_ids(self):
        new_words = set(
            word['reading'] for word in self._get_tracked_words()
            if (
                word['is_new']
                and word['jmdict_id'] is None
            )
        )
        new_words -= self.learning_words_without_jmdict_ids
        new_words -= self.known_words_without_jmdict_ids
        return new_words

    @cached_property
    def learning_words_without_jmdict_ids(self):
        learning_words = set(
            word['reading'] for word in self._get_tracked_words()
            if (
                not word['is_new']
                and not word['is_mature']
                and word['jmdict_id'] is None
            )
        )
        learning_words -= self.known_words_without_jmdict_ids
        return learning_words

    @cached_property
    def known_words_without_jmdict_ids(self):
        return set(
            word['reading'] for word in self._get_tracked_words()
            if (
                word['is_mature']
                and word['jmdict_id'] is None
            )
        )
