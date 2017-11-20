import random
from datetime import (
    datetime,
    timedelta,
)

from cachecow.decorators import cached_function
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.db.models import (
    Avg,
    Count,
    Max,
    Min,
    Sum,
)

from constants import (
    ALL_GRADES,
    GRADE_NAMES,
    GRADE_NONE,
    MATURE_INTERVAL_MIN,
    MAX_NEW_CARD_ORDINAL,
    MIN_CARD_SPACE,
    CARD_SPACE_FACTOR,
    PRODUCTION,
    RECOGNITION,
    KANJI_READING,
    KANJI_WRITING,
)
from manabi.apps.flashcards.cachenamespaces import (
    deck_review_stats_namespace,
    fact_grid_namespace,
)
from manabi.apps.flashcards.models.cardmanager import CardQuerySet
from manabi.apps.flashcards.models.undo import UndoCardReview
from repetitionscheduler import repetition_algo_dispatcher

CARD_TEMPLATE_CHOICES = (
    (PRODUCTION, 'Production'),
    (RECOGNITION, 'Recognition'),
    (KANJI_READING, 'Kanji Reading'),
    (KANJI_WRITING, 'Kanji Writing'),
)


class Card(models.Model):
    '''
    Remember to migrate undo histories with Card migrations.
    '''
    objects = CardQuerySet.as_manager()

    # Denormalized fields:
    owner = models.ForeignKey(User, editable=False)
    deck = models.ForeignKey('flashcards.Deck', db_index=True)
    deck_suspended = models.BooleanField(default=False, db_index=True)

    fact = models.ForeignKey('flashcards.Fact', db_index=True)

    template = models.SmallIntegerField(choices=CARD_TEMPLATE_CHOICES, blank=False)

    # False when the card is removed from the Fact. This way, we can keep
    # card statistics if enabled later.
    active = models.BooleanField(default=True, db_index=True)

    ease_factor = models.FloatField(null=True, blank=True)
    interval = models.DurationField(null=True, blank=True, db_index=True)
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_ease_factor = models.FloatField(null=True, blank=True)
    last_interval = models.DurationField(null=True, blank=True)
    last_due_at = models.DateTimeField(null=True, blank=True)

    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    last_review_grade = models.PositiveIntegerField(null=True, blank=True)
    last_failed_at = models.DateTimeField(null=True, blank=True)

    #TODO-OLD use this for is_new
    review_count = models.PositiveIntegerField(default=0, editable=False)

    new_card_ordinal = models.PositiveIntegerField(null=True, blank=True)

    suspended = models.BooleanField(default=False, db_index=True)

    class Meta:
        app_label = 'flashcards'
        index_together = [
            ['owner', 'due_at', 'active', 'suspended'],
            ['deck', 'owner'],
        ]

    def __unicode__(self):
        return u'{} | {} [{}]'.format(self.fact.expression, self.fact.meaning, self.template)

    def save(self, force_update=False, update_fields=None, *args, **kwargs):
        if update_fields is None and not force_update:
            self.owner_id = self.deck.owner_id

        if update_fields is None or {'deck', 'deck_id'} & set(update_fields):
            self.deck_suspended = self.deck.suspended

        if (
            update_fields is not None  # Too slow to do this on every save.
            and {'deck', 'deck_id', 'suspended', 'active'} & set(update_fields)
        ):
            self.deck.refresh_card_count()

        is_new = self.pk is None

        super(Card, self).save(
            force_update=force_update, update_fields=update_fields,
            *args, **kwargs)

        if is_new:
            self.deck.refresh_card_count()

    def copy(self, target_fact, owner_id=None):
        '''
        Returns a new Card object. Copies for the purpose of subscribing.
        '''
        if owner_id is None:
            owner_id = target_fact.owner.id
        return Card(
            owner_id=owner_id,
            deck_id=target_fact.deck_id,
            fact=target_fact,
            template=self.template,
            active=self.active,
            suspended=self.suspended,
            new_card_ordinal=self.new_card_ordinal,
        )

    @property
    def redis(self):
        from manabi.apps.flashcards.models.redis_models import RedisCard
        return RedisCard(self)

    @property
    def siblings(self):
        '''Returns the other cards from this card's fact.'''
        return self.fact.card_set.exclude(id=self.id)

    @property
    def first_reviewed_at(self):
        key = '.'.join(['Card', self.id, 'first_reviewed_at'])
        val = cache.get(key)
        if val is None:
            val = self.cardhistory_set.aggregate(
                    Min('reviewed_at'))['reviewed_at__min']
            cache.set(key, val)
        return val

    @property
    def last_review_grade_name(self):
        '''Returns a string version of the last review grade.'''
        return GRADE_NAMES.get(self.last_review_grade)

    def update_due_at(self, due_at, update_last_due_at=True):
        if update_last_due_at:
            self.last_due_at, self.due_at = (
                self.due_at, due_at)
        else:
            self.due_at = due_at

    @classmethod
    def random_card_ordinal(cls):
        return random.randrange(0, MAX_NEW_CARD_ORDINAL)

    def randomize_new_order(self):
        '''
        Randomizes the order of this card, for selecting new cards.
        '''
        self.new_card_ordinal = self.random_card_ordinal()
        self.save()

    def activate(self):
        from manabi.apps.flashcards.signals import card_active_field_changed

        self.active = True
        self.save()
        card_active_field_changed.send(self, instance=self)

    def deactivate(self):
        from manabi.apps.flashcards.signals import card_active_field_changed

        self.active = False
        self.save(update_fields=['active'])
        card_active_field_changed.send(self, instance=self)

    @property
    def is_new(self):
        '''Returns whether this card has been reviewed before.'''
        return self.last_reviewed_at is None

    def is_mature(self):
        return self.interval >= MATURE_INTERVAL_MIN

    def is_due(self, time=None):
        '''Returns True if this card's due date is in the past.'''
        #TODO-OLD why would is_new ever be True and self.due_at be none?
        if time is None: time = datetime.utcnow()

        if self.is_new or not self.due_at:
            return False
        return self.due_at < time

    @cached_function(namespace=deck_review_stats_namespace)
    def average_duration(self):
        '''
        The average duration spent on the card each time it is shown
        (seconds, floating-point).
        '''
        return self.cardhistory_set.aggregate(
                Avg('duration'))['duration__avg']

    @cached_function(namespace=deck_review_stats_namespace)
    def total_duration(self):
        '''
        Total duration spent on the card each time it is shown.
        '''
        return self.cardhistory_set.aggregate(
                Sum('duration'))['duration__sum']

    @cached_function(namespace=deck_review_stats_namespace)
    def average_question_duration(self):
        '''
        Returns the average duration spent looking at the question side of
        this card before viewing the answer (in seconds, floating point).
        '''
        return self.cardhistory_set.aggregate(
                Avg('question_duration'))['question_duration__avg']

    @cached_function(namespace=deck_review_stats_namespace)
    def total_question_duration(self):
        '''
        The total time spent thinking of the answer.
        '''
        return self.cardhistory_set.aggregate(
                Sum('question_duration'))['question_duration__sum']

    def calculated_interval(self):
        '''
        The `interval` property of a card doesn't necessarily decide the
        time between the review and the due date - it's used as a basis
        for calculating the due date, but other factors may apply.

        This returns the actual time between last review and due date.
        This is the time the user was supposed to wait.
        '''
        if not self.is_new and self.due_at is not None:
            return self.due_at - self.last_reviewed_at

    def sibling_spacing(self):
        '''
        Calculate the minimum space between this card and its siblings
        that should be enforced (not necessarily actual,
        if the user chooses to review early).

        The space is `space_factor` times this card's interval,
        or `min_card_space` at minimum.

        Returns a timedelta.

        TODO-OLD: maybe this should be more dependent on each card or something
        TODO-OLD: also maybe a max space if dependent on other cards' intervals
        '''
        if self.interval is None:
            return MIN_CARD_SPACE

        min_space = max(
            MIN_CARD_SPACE,
            timedelta(seconds=
                      CARD_SPACE_FACTOR * self.interval.total_seconds())
        )
        return min_space

    def delay(self, duration):
        '''
        This card's due date becomes `duration` (a timedelta) days from
        now, or from its due date if not yet due.

        This is for when this card is due at the same time as a sibling
        card (a card from the same fact).
        '''
        now = datetime.utcnow()
        from_date = self.due_at if self.due_at >= now else now
        self.update_due_at(from_date + duration, update_last_due_at=False)
        #self.redis.update_due_at()

    def next_repetition_per_grade(self, reviewed_at=None):
        #FIXME disable fuzzing
        if not reviewed_at:
            reviewed_at = datetime.utcnow()

        reps = {}
        for grade in ALL_GRADES:
            repetition_algo = repetition_algo_dispatcher(
                self, grade, reviewed_at=reviewed_at)
            reps[grade] = repetition_algo.next_repetition()
        return reps

    def _update_statistics(self, grade, reviewed_at,
                           duration=None, question_duration=None):
        '''
        Updates this card's stats. Call this for each review,
        before applying the new review. After applying the new review,
        some other CardHistory fields can be filled in. The reason we do
        this in 2 parts is that our undo system needs to know about this
        object, but it creates the undo object before the card object gets
        updated with the new review stats, so that we can rollback to it.

        See the `self.review` docstring for info on `duration`
        and `question_duration`.
        '''
        from cardhistory import CardHistory

        #TODO-OLD update CardStatistics
        was_new = self.is_new

        card_history_item = CardHistory(
            card=self, response=grade, reviewed_at=reviewed_at, was_new=was_new)
        card_history_item.save()

        self.review_count += 1

        return card_history_item

    def _apply_updated_schedule(self, next_repetition):
        '''
        Updates this card's scheduling with values for the next repetition.

        `next_repetition` should have the following fields:
            `interval`, `ease_factor`, `due_at`

        (See `NextRepetition` class)
        '''
        self.last_ease_factor, self.ease_factor = (
            self.ease_factor, next_repetition.ease_factor)
        self.last_interval, self.interval = (
            self.interval, next_repetition.interval)
        self.update_due_at(next_repetition.due_at)

        # self.redis.update_ease_factor()

    def review(self, grade, duration=None, question_duration=None):
        '''
        Commits a review rated with `grade`.

        `question_duration` is an optional parameter which contains the
        time (in seconds, floating point) that the user spent looking at the
        question/front side of the card, before hitting "Show Answer" to
        see the back. It is in effect the time spent thinking of the answer.

        `duration` is the same, but for each entire duration of viewing
        this card (so, the time taken for the front and back of the card.)
        '''
        from manabi.apps.flashcards.signals import pre_card_reviewed, post_card_reviewed

        pre_card_reviewed.send(self, instance=self)

        reviewed_at = datetime.utcnow()
        was_new = self.is_new

        # Update this card's statistics
        card_history_item = self._update_statistics(
            grade, reviewed_at,
            duration=duration, question_duration=question_duration)

        # Create Undo stack item
        UndoCardReview.objects.add_undo(card_history_item)

        # Compute and apply updated card repetition values.
        repetition_algo = repetition_algo_dispatcher(
            self, grade, reviewed_at=reviewed_at)
        repetition_algo.next_repetition.delete_cache(repetition_algo)
        next_repetition = repetition_algo.next_repetition()
        self._apply_updated_schedule(next_repetition)

        self.last_review_grade = grade
        self.last_reviewed_at  = reviewed_at

        if grade == GRADE_NONE:
            self.last_failed_at = reviewed_at

        # Finish up the card history item record
        card_history_item.ease_factor = self.ease_factor
        card_history_item.interval    = self.interval
        card_history_item.save()

        self.save()
        # self.redis.after_review()
        post_card_reviewed.send(self, instance=self)
