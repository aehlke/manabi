# -*- coding: utf-8 -*-

from datetime import datetime

from django.utils.lru_cache import lru_cache

from manabi.apps.flashcards.models.constants import (
    NEW_CARDS_PER_DAY_LIMIT_OVERRIDE_INCREMENT,
)
from manabi.apps.flashcards.models.new_cards_limit import (
    NewCardsLimit,
)
from manabi.apps.flashcards.models.review_availability_prompts import (
    review_availability_prompts,
)
from manabi.apps.flashcards.models import (
    Deck,
    Fact,
    Card,
)


class ReviewAvailabilities(object):
    def __init__(
        self,
        user,
        deck=None,
        new_cards_per_day_limit_override=None,
        buffered_new_cards_count=0,
        excluded_card_ids=set(),
        time_zone=None,
        new_cards_limit=None,
    ):
        '''
        `buffered_new_cards_count` are the count of new cards that the user
        is already about to study (e.g. the cards in front of the appearance
        of these availabilities, if on an interstitial). They're effectively
        counted as if they were already reviewed, with respect to this class's
        calculations.

        `new_cards_limit` is an instance of `NewCardsLimit.`
        '''
        self.user = user
        self.time_zone = time_zone
        self.deck = deck
        self.excluded_card_ids = excluded_card_ids
        self._buffered_new_cards_count = buffered_new_cards_count

        self._new_cards_limit = (
            new_cards_limit or
            NewCardsLimit(
                user,
                new_cards_per_day_limit_override = (
                    new_cards_per_day_limit_override),
                buffered_new_cards_count=buffered_new_cards_count,
                time_zone=time_zone,
            )
        )

    @property
    def base_cards_queryset(self):
        cards = Card.objects.available().of_user(self.user)

        if self.deck:
            cards = cards.of_deck(self.deck)

        if self.excluded_card_ids:
            cards = cards.excluding_ids(self.excluded_card_ids)

        return cards

    @property
    @lru_cache(maxsize=None)
    def ready_for_review(self):
        if self.user.is_anonymous():
            return False

        return (
            self.base_cards_queryset
                .of_user(self.user)
                .available()
                .due()
                .exists()
        )

    @property
    @lru_cache(maxsize=None)
    def _next_new_cards_limit(self):
        if self.new_cards_per_day_limit_reached:
            return NEW_CARDS_PER_DAY_LIMIT_OVERRIDE_INCREMENT
        else:
            return self._new_cards_limit.next_new_cards_limit

    @property
    @lru_cache(maxsize=None)
    def next_new_cards_count(self):
        '''
        If the user is beyond their daily limit, this provides up to the
        next override limit.
        '''
        if self.user.is_anonymous():
            return 0

        available_count = self.base_cards_queryset.new_count(
            self.user,
            including_buried=False,
        )

        return max(
            0,
            min(available_count,
                self._next_new_cards_limit - self._buffered_new_cards_count),
        )

    @property
    def buried_new_cards_count(self):
        '''
        `None` means unspecified; not used if `next_new_cards_count` > 0.
        '''
        if self.user.is_anonymous():
            return None

        if self.next_new_cards_count > 0:
            return None

        available_count = self.base_cards_queryset.new_count(
            self.user,
            including_buried=True,
        )

        return max(
            0,
            min(available_count,
                self._next_new_cards_limit - self._buffered_new_cards_count),
        )

    @property
    def new_cards_per_day_limit_reached(self):
        return self._new_cards_limit.new_cards_per_day_limit_reached

    @property
    @lru_cache(maxsize=None)
    def new_cards_per_day_limit_override(self):
        '''
        If the user wants to continue learning new cards beyond the daily
        limit, this value provides the overridden daily limit to use (based
        off `next_new_cards_count`).
        '''
        if not self.new_cards_per_day_limit_reached:
            return None
        return (
            self._new_cards_limit.reviewed_today_count +
            NEW_CARDS_PER_DAY_LIMIT_OVERRIDE_INCREMENT
        )

    @property
    @lru_cache(maxsize=None)
    def early_review_available(self):
        if self.user.is_anonymous():
            return False

        return self.base_cards_queryset.filter(
            due_at__gt=datetime.utcnow()
        ).exists()

    @lru_cache(maxsize=None)
    def _prompts(self):
        if self.user.is_anonymous():
            return ("", "")

        if self.user.username in ['alex', 'alextest']:
            return review_availability_prompts(self)

        return (
            u"This text will tell you about the cards ready for you to learn or review.",
            u"I haven't built this part of the backend API yet—this is beta, it'll come before release!"
        )

    @property
    def primary_prompt(self):
        return self._prompts()[0]

    @property
    def secondary_prompt(self):
        return self._prompts()[1]
