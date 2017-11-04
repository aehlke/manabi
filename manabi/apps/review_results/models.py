from datetime import datetime, timedelta

from django.conf import settings
from django.db.models.functions import TruncDay
import pytz

from manabi.apps.flashcards.models import CardHistory


_WEEKS_TO_REPORT = 9


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
    def days_reviewed_by_week(self):
        start_of_today = datetime.now(self.user_timezone)
        if start_of_today.hour < settings.START_OF_DAY:
            start_of_today -= timedelta(days=1)
        start_of_today.hour = settings.START_OF_DAY

        if now.isoweekday() == 7:
            week_sunday = now
        else:
            week_sunday = now - timedelta(days=now.isoweekday())

        week_sunday_utc = week_sunday.astimezone(pytz.utc)

        review_days = set(self._card_history
            .filter(reviewed_at__day__gte=(
                week_sunday_utc - timedelta(weeks=_WEEKS_TO_REPORT)))
            .annotate(reviewed_day=
                TruncDay('reviewed_at', tzinfo=self.user_timezone))
            .values('reviewed_day')
            .distinct()
            .order_by('reviewed_day')
            .values_list('reviewed_day', flat=True)
        )

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
