from django.utils.lru_cache import lru_cache

from manabi.apps.flashcards.models import (
    CardHistory,
)
from manabi.apps.flashcards.models.constants import (
    DEFAULT_TIME_ZONE,
    NEW_CARDS_PER_DAY_LIMIT,
)


class NewCardsLimit(object):
    '''
    How many more new cards can the user learn today?
    '''

    def __init__(
        self,
        user,
        new_cards_per_day_limit_override=None,
        buffered_new_cards_count=0,
        time_zone=None,
    ):
        self.user = user
        self.new_cards_per_day_limit_override = (
            new_cards_per_day_limit_override)
        self.buffered_new_cards_count = buffered_new_cards_count
        self.time_zone = time_zone

    @property
    @lru_cache(maxsize=None)
    def new_cards_per_day_limit_reached(self):
        return self._per_day_limit() - self.learned_today_count <= 0

    @property
    @lru_cache(maxsize=None)
    def learned_today_count(self):
        return (
            CardHistory.objects
            .of_day_for_user(self.user, self.time_zone or DEFAULT_TIME_ZONE)
            .filter(was_new=True)
            .count()
        ) + self.buffered_new_cards_count

    @property
    @lru_cache(maxsize=None)
    def next_new_cards_limit(self):
        return max(
            0,
            self._per_day_limit() - self.learned_today_count,
        )

    @property
    @lru_cache(maxsize=None)
    def next_new_cards_count(self):
        if self.user.is_anonymous():
            return 0

        new_card_count = self._base_cards_queryset.new_count(self.user)

        remaining = max(
            0, min(
                new_card_count,
                self._per_day_limit() - self.learned_today_count
            ),
        )
        return remaining

    def _per_day_limit(self):
        if self.new_cards_per_day_limit_override is None:
            return NEW_CARDS_PER_DAY_LIMIT
        else:
            return self.new_cards_per_day_limit_override
