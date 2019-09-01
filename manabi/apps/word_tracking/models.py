from django.contrib.admin.utils import flatten
from django.db import models
from django.db.models import Case, When, Value, F, Max
from django.db.models.functions import Greatest
from django.utils.functional import cached_property

from manabi.apps.flashcards.models import Fact, Card
from manabi.apps.flashcards.models.constants import (
    MATURE_INTERVAL_MIN,
)
from manabi.apps.utils.japanese import is_kanji


def _kanji_in_reading(reading):
    kanji = set()
    for char in reading:
        if is_kanji(char):
            kanji.add(char)
    return [c for c in kanji]


class TrackedWords:
    def __init__(self, user):
        self.user = user
        self._tracked_words = None

    def _get_cards(self):
        return Card.objects.filter(
            owner=self.user,
            active=True,
        )

    def _get_tracked_words(self):
        '''
        Includes suspended cards (that the user may have already reviewed).
        '''
        if self._tracked_words is None:
            self._tracked_words = self._get_cards().annotate(
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
                reading=F('fact__reading'),
            ).distinct().values(
                'jmdict_id', 'reading', 'is_new', 'is_mature',
                'suspended', 'deck_suspended')
        return self._tracked_words

    def last_modified(self):
        return self._get_cards().annotate(
            last_modified=Greatest(
                'last_reviewed_at',
                'created_or_modified_at',
            )
        ).aggregate(Max('last_modified'))['last_modified__max']

    @cached_property
    def suspended_jmdict_ids(self):
        return set(
            word['jmdict_id'] for word in self._get_tracked_words()
            if (word['suspended'] or word['deck_suspended'])
            and word['jmdict_id'] is not None
        )

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
    def suspended_words_without_jmdict_ids(self):
        return set(
            word['reading'] for word in self._get_tracked_words()
            if (word['suspended'] or word['deck_suspended'])
            and word['jmdict_id'] is None
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

    @cached_property
    def learning_kanji(self):
        learning_kanji = set(flatten([
            _kanji_in_reading(word['reading'])
            for word in self._get_tracked_words()
            if (
                not word['is_new']
                and not word['is_mature']
            )
        ]))
        learning_kanji -= set(self.known_kanji)
        return ''.join(learning_kanji)

    @cached_property
    def known_kanji(self):
        return ''.join(set(flatten([
            _kanji_in_reading(word['reading'])
            for word in self._get_tracked_words()
            if word['is_mature']
        ])))
