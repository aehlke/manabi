import dateutil.tz
from datetime import datetime, date, timedelta

import pytz
from django.conf import settings
from django.db.models.functions import TruncDay
from django.utils.lru_cache import lru_cache

from manabi.apps.flashcards.models import CardHistory


_WEEKS_TO_REPORT = 9


def _start_of_today(user_timezone):
    start_of_today = datetime.now(user_timezone)
    if start_of_today.hour < settings.START_OF_DAY:
        start_of_today -= timedelta(days=1)
    return start_of_today.replace(hour=settings.START_OF_DAY)


class ReviewResults(object):
    '''
    Results for the last review session.
    '''
    def __init__(self, user, user_timezone, review_began_at):
        self.user = user
        self.user_timezone = user_timezone
        self.review_began_at = review_began_at
        self._card_history = (CardHistory.objects
            .of_user(user)
            .filter(reviewed_at__gte=review_began_at)
        )

    @property
    def cards_reviewed(self):
        return self._card_history.count()

    @property
    def current_daily_streak(self):
        start_of_today = _start_of_today(self.user_timezone)
        day_to_check = start_of_today.date()

        streak = 0
        while True:
            if day_to_check not in self._days_reviewed():
                return streak
            day_to_check -= timedelta(days=1)
            streak += 1


    @lru_cache(maxsize=None)
    def _days_reviewed(self):
        return set(self._card_history
            .annotate(reviewed_day=
                TruncDay('reviewed_at', tzinfo=dateutil.tz.tzoffset(
                    self.user_timezone, settings.START_OF_DAY)))
            .values('reviewed_day')
            .distinct()
            .order_by('reviewed_day')
            .values_list('reviewed_day', flat=True)
        )

    @property
    def days_reviewed_by_week(self):
        start_of_today = _start_of_today(self.user_timezone)

        if start_of_today.isoweekday() == 7:
            week_sunday = start_of_today
        else:
            week_sunday = (
                start_of_today
                - timedelta(days=start_of_today.isoweekday())
            )

        review_days = self._days_reviewed()
        weeks = []
        for week_delta in range(0, _WEEKS_TO_REPORT):
            days_reviewed = sum(
                1 for day in [
                    (week_sunday + timedelta(days=day_offset))
                    for day_offset
                    in range(0, 7)
                ]
                if day in review_days
            )

            week = {
                'week': '{}/{}'.format(week_sunday.month, week_sunday.day),
                'days_reviewed': days_reviewed,
            }

        return weeks
