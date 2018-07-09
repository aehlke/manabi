from django.db.models.query import QuerySet
from django.db import models
from django.db.models import Count, Min, Max, Sum, Avg

from manabi.apps.utils.time_utils import start_and_end_of_day
from .constants import MATURE_INTERVAL_MIN


class CardHistoryManagerMixin:
    def of_user(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(card__owner=user)

    def of_deck(self, deck):
        return self.filter(card__fact__deck=deck)

    def new(self):
        return self.filter(was_new=True)

    def young(self):
        return self.filter(was_new=False, interval__lt=MATURE_INTERVAL_MIN)

    def mature(self):
        return self.filter(interval__gte=MATURE_INTERVAL_MIN)

    def with_reviewed_on_dates(self):
        '''
        Adds a `reviewed_on` field to the selection which is extracted
        from the `reviewed_at` datetime field.
        '''
        return self.extra(select={'reviewed_on': 'date(reviewed_at)'})

    def of_day_for_user(
        self, user, time_zone, date=None, field_name='reviewed_at'
    ):
        '''
        Filters on the start and end of day for `user` adjusted to UTC.

        `date` is a date object. Defaults to today.
        '''
        start, end = start_and_end_of_day(user, time_zone, date=date)
        kwargs = {field_name + '__range': (start, end)}
        return self.of_user(user).filter(**kwargs)


class CardHistoryStatsMixin:
    '''Stats data methods for use in graphs.'''

    def repetitions(self):
        '''
        Returns a list of dictionaries,
        with values 'date' and 'repetitions', the count of reps that day.
        '''
        return self.with_reviewed_on_dates().values(
            'reviewed_on').order_by().annotate(
            repetitions=Count('id'))

    def daily_duration(self, user, date=None):
        '''

        Returns the time spent reviewing on the given date
        (defaulting to today) for `user`, in seconds.
        '''
        items = self.of_user(user).of_day_for_user(user, date=date)
        return items.aggregate(Sum('duration'))['duration__sum']


class CardHistoryQuerySet(
    CardHistoryManagerMixin, CardHistoryStatsMixin, QuerySet,
):
    pass


class CardHistory(models.Model):
    objects = CardHistoryQuerySet.as_manager()

    card = models.ForeignKey('Card', models.CASCADE)
    # TODO: Denormalize card owner here.

    response = models.PositiveIntegerField(editable=False)
    reviewed_at = models.DateTimeField()

    ease_factor = models.FloatField(null=True, blank=True)
    interval = models.DurationField(null=True, blank=True)

    # Was the card new when it was reviewed this time?
    was_new = models.BooleanField(default=False, db_index=True)

    class Meta:
        app_label = 'flashcards'
        index_together = [
            ['card', 'was_new', 'reviewed_at'],
        ]
