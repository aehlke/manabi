# -*- coding: utf-8 -*-

from datetime import datetime

from django.utils.lru_cache import lru_cache

from manabi.apps.flashcards.models.constants import (
    NEW_CARDS_PER_DAY_LIMIT_OVERRIDE_INCREMENT,
    TRIAL_DAILY_REVIEW_CAP,
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
from manabi.apps.flashcards.models.trial_limits import (
    cards_remaining_in_daily_trial,
)
from manabi.apps.subscriptions.models import user_is_active_subscriber


class ReviewAvailabilities:
    def __init__(
        self,
        user,
        deck=None,
        new_cards_per_day_limit_override=None,
        early_review_began_at=None,
        buffered_cards_count=0,
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
        self.early_review_began_at = early_review_began_at
        self._buffered_cards_count = buffered_cards_count
        self._buffered_new_cards_count = buffered_new_cards_count

        self.new_cards_limit = (
            new_cards_limit or
            NewCardsLimit(
                user,
                new_cards_per_day_limit_override=(
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
        else:
            cards = cards.exclude(deck_suspended=True)

        if self.excluded_card_ids:
            cards = cards.excluding_ids(self.excluded_card_ids)

        return cards

    @property
    @lru_cache(maxsize=None)
    def ready_for_review(self):
        if self.user.is_anonymous:
            return False

        return self.base_cards_queryset.due().exists()

    @property
    @lru_cache(maxsize=None)
    def _buried_fact_ids(self):
        return Fact.objects.buried(
            self.user, excluded_card_ids=self.excluded_card_ids,
        ).values_list('id', flat=True)

    @property
    @lru_cache(maxsize=None)
    def _next_new_cards_limit(self):
        if self.new_cards_per_day_limit_reached:
            return NEW_CARDS_PER_DAY_LIMIT_OVERRIDE_INCREMENT
        else:
            return self.new_cards_limit.next_new_cards_limit

    @property
    @lru_cache(maxsize=None)
    def next_new_cards_count(self):
        '''
        If the user is beyond their daily limit, this provides up to the
        next override limit.
        '''
        if self.user.is_anonymous:
            return 0

        available_count = self.base_cards_queryset.new_count(
            self.user,
            including_buried=False,
            buried_fact_ids=self._buried_fact_ids,
        )

        return max(
            0,
            min(available_count,
                self._next_new_cards_limit - self._buffered_new_cards_count),
        )

    @property
    @lru_cache(maxsize=None)
    def buried_new_cards_count(self):
        '''
        `None` means unspecified; not used if `next_new_cards_count` > 0.
        '''
        if self.user.is_anonymous:
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
        return self.new_cards_limit.new_cards_per_day_limit_reached

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
        if (
            self.next_new_cards_count == 0
            and self.buried_new_cards_count == 0
            and not self.base_cards_queryset.new(self.user).exists()
        ):
            return None
        return (
            self.new_cards_limit.learned_today_count +
            NEW_CARDS_PER_DAY_LIMIT_OVERRIDE_INCREMENT
        )

    @property
    @lru_cache(maxsize=None)
    def early_review_available(self):
        '''
        Mutually-exclusive with readiness for review (is false if any cards
        are due).
        '''
        if self.user.is_anonymous:
            return False

        if self.ready_for_review:
            return False

        return self.base_cards_queryset.filter(
            due_at__gt=datetime.utcnow(),
        ).exists()

    @property
    def invalidated_upon_card_failure(self):
        '''
        Indicates that these availabilities ought to be eliminated from the UI
        as soon as the user fails any reviews.
        '''
        return True

    @lru_cache(maxsize=None)
    def _prompts(self):
        if self.user.is_anonymous:
            return ("", "")
        return review_availability_prompts(self)

    @property
    def primary_prompt(self):
        return self._prompts()[0]

    @property
    def secondary_prompt(self):
        return self._prompts()[1]

    @property
    @lru_cache(maxsize=None)
    def _cards_remaining_in_daily_trial(self):
        cards_remaining = cards_remaining_in_daily_trial(
            self.user, time_zone=self.time_zone)
        if cards_remaining is None:
            return None

        return max(0, cards_remaining - self._buffered_cards_count)

    @property
    @lru_cache(maxsize=None)
    def trial_prompt(self):
        if self.user.is_anonymous:
            return
        if user_is_active_subscriber(self.user):
            return
        if self._cards_remaining_in_daily_trial is None:
            return

        return (
            "You have {} out of {} cards left today.\n"
            "Purchase to unlock unlimited daily reviews!"
        ).format(
            self._cards_remaining_in_daily_trial,
            TRIAL_DAILY_REVIEW_CAP,
        )

    @property
    @lru_cache(maxsize=None)
    def trial_limit_reached(self):
        if self.user.is_anonymous:
            return False
        if user_is_active_subscriber(self.user):
            return False
        cards_remaining = self._cards_remaining_in_daily_trial
        return cards_remaining == 0
