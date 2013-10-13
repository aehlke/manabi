from django.db.models import Count, Min, Max, Sum, Avg
from model_utils.managers import manager_from
from manabi.apps.utils.usertime import start_and_end_of_day
from constants import MATURE_INTERVAL_MIN
from django.db import models


class CardHistoryManagerMixin(object):
    def of_user(self, user):
        return self.filter(card__fact__deck__owner=user)

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

    def of_day(self, user, date=None, field_name='reviewed_at'):
        '''
        Filters on the start and end of day for `user` adjusted to UTC.

        `date` is a date object. Defaults to today.
        '''
        start, end = start_and_end_of_day(user, date=None)

        kwargs = {field_name + '__range': (start, end)}
        return self.filter(**kwargs)
    


class CardHistoryStatsMixin(object):
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
        items = self.of_user(user).of_day(user, date=date)
        return items.aggregate(Sum('duration'))['duration__sum']



CardHistoryManager = lambda: manager_from(
    CardHistoryManagerMixin, CardHistoryStatsMixin)

class CardHistory(models.Model):
    objects = CardHistoryManager()

    card = models.ForeignKey('Card')

    response = models.PositiveIntegerField(editable=False)
    reviewed_at = models.DateTimeField()

    ease_factor = models.FloatField(null=True, blank=True)
    interval = models.FloatField(null=True, blank=True, db_index=True) #days

    # Was the card new when it was reviewed this time?
    was_new = models.BooleanField(default=False, db_index=True) 

    question_duration = models.FloatField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)

    class Meta:
        app_label = 'flashcards'

