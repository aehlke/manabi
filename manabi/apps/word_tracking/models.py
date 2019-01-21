from django.db import models
from django.db.models import Case, When, Value, F

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
            ).distinct().values('jmdict_id', 'reading', 'is_mature')
        print(self._tracked_words)
        return self._tracked_words

    @property
    def learning_jmdict_ids(self):
        return [
            word['jmdict_id'] for word in self._get_tracked_words()
            if not word['is_mature'] and word['jmdict_id'] is not None
        ]

    @property
    def known_jmdict_ids(self):
        return [
            word['jmdict_id'] for word in self._get_tracked_words()
            if word['is_mature'] and word['jmdict_id'] is not None
        ]

    @property
    def learning_words_without_jmdict_ids(self):
        return [
            word['reading'] for word in self._get_tracked_words()
            if not word['is_mature'] and word['jmdict_id'] is None
        ]

    @property
    def known_words_without_jmdict_ids(self):
        return [
            word['reading'] for word in self._get_tracked_words()
            if word['is_mature'] and word['jmdict_id'] is None
        ]
