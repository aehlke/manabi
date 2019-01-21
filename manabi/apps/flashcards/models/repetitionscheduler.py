from datetime import timedelta, datetime
from math import cos, pi
import random

from cachecow.decorators import cached_function
from django.utils.lru_cache import lru_cache

from .constants import (
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY, MATURE_INTERVAL_MIN)
from manabi.apps.flashcards.models.intervals import initial_interval
from manabi.apps.utils.utils import timedelta_to_float


def _multiply_timedelta(duration, factor):
    return timedelta(
        seconds=duration.total_seconds() * factor)


def repetition_algo_dispatcher(card, *args, **kwargs):
    '''
    Returns a `RepetitionAlgo` (or one of its subclasses) instance
    corresponding to the given `card`.

    See `RepetitionAlgo` for documentation on the arguments.
    '''
    # New card?
    if card.is_new:
        cls = NewCardAlgo
    # Last review was a failure?
    elif card.last_review_grade == GRADE_NONE:
        cls = FailedCardAlgo
    # Young card.
    elif card.interval < MATURE_INTERVAL_MIN:
        cls = YoungCardAlgo
    # Mature card.
    else:
        cls = MatureCardAlgo

    return cls(card, *args, **kwargs)


class RepetitionAlgo:
    '''
    This base class represents the most general kind of card, which does
    not take into account special cases of having been recently failed,
    or being brand new, and so on. It is general enough that its implemented
    methods can be reused selectively by child implementations in order to
    handle the special case conditions as applied to the base case.
    '''

    # Only used when decks have no average EF yet.
    DEFAULT_EASE_FACTOR = 2.5

    # These are the precomputed values, so that we can modify them
    # independently later to test their effectiveness.
    EASE_FACTOR_MODIFIERS = {
        GRADE_NONE: -0.3, #TODO-OLD more accurate grade_none value
        GRADE_HARD: -0.1401,
        GRADE_GOOD:  0.0,
        GRADE_EASY:  0.1,
    }

    GRADE_EASY_BONUS_FACTOR = 0.2

    # Factor to reduce a bonus by for non-easy grades
    HARD_BONUS_REDUCER = 4.0
    GOOD_BONUS_REDUCER = 2.0

    # Max interval bonus factor
    INTERVAL_BONUS_FACTOR_CAP = 2.0

    # When intervals are set, they are fuzzed by at most this value, -/+
    INTERVAL_FUZZ_MAX = 0.035

    MINIMUM_EASE_FACTOR = 1.3

    YOUNG_FAILURE_INTERVAL = timedelta(
        days=(1.0 / (24.0 * 60.0)) * 10.0) # 10 mins

    MATURE_FAILURE_INTERVAL = timedelta(days=1.0)

    #TODO-OLD MATURE_FAILURE_INTERVAL should not be a constant value,
    #     but dependent on other factors of a given card
    #TODO-OLD 'tomorrow' should also be dependent on the current time,
    #     instead of just 1 day from now

    # Ease Factor to use temporarily when penalizing for "hard" grades,
    # to be more aggressive.
    HARD_GRADE_PENALTY_EF = 1.2

    def __init__(self, card, grade, reviewed_at=None):
        '''
        Computes the next repetition for a card that is going to be (or has
        already been) reviewed.

        `reviewed_at` defaults to now.
        '''
        self.card = card
        self.grade = grade
        self.reviewed_at = reviewed_at or datetime.utcnow()

    def next_repetition(self):
        '''
        Returns an instance of `NextRepetition` containing the updated
        repetition values for this card.

        Avoid calling this unnecessarily without caching.
        '''
        interval = self._next_interval()
        ease_factor = self._next_ease_factor()
        due_at = self._next_due_at()

        return NextRepetition(self.card, interval, ease_factor, due_at)

    def _next_interval(self, failure_interval=timedelta()):
        '''
        Returns an interval.
        '''
        #TODO-OLD fuzz the results
        current_interval = self.card.interval
        ease_factor = self.card.ease_factor

        # Review failure.
        if self.grade == GRADE_NONE:
            # Reset the interval to an initial value.
            next_interval = failure_interval
            #TODO-OLD how to handle failures on new cards? should it keep its
            # 'new' status, and should the EF change?
            #TODO-OLD handle failures of cards that are reviewed early
            # differently somehow
            #TODO-OLD penalize even worse if it was reviewed early
            # and still failed
        # Successful review.
        else:
            # Late review (or approx. on time)
            if self.card.due_at and self._percent_waited() > 1.0:
                # Give a bonus for getting it right later than expected.
                bonus_factor = self._percent_waited()

                # Less bonus for non-easy grades.
                def reduce_bonus(reduction_factor):
                    return ((bonus_factor - 1.0) / reduction_factor) + 1.0

                if self.grade == GRADE_HARD:
                    bonus_factor = reduce_bonus(self.HARD_BONUS_REDUCER)
                elif self.grade == GRADE_GOOD:
                    bonus_factor = reduce_bonus(self.GOOD_BONUS_REDUCER)

                # Cap the bonus.
                bonus_factor = min(self.INTERVAL_BONUS_FACTOR_CAP,
                                   bonus_factor)

                assert bonus_factor >= 1.0

                # Apply the bonus.
                current_interval = _multiply_timedelta(
                    current_interval, bonus_factor)

            # Penalize hard grades.
            if self.grade == GRADE_HARD:
                ease_factor = self.HARD_GRADE_PENALTY_EF

            # Update interval.
            next_interval = _multiply_timedelta(
                current_interval, ease_factor)

            # Give a bonus to easy grades.
            if self.grade == GRADE_EASY:
                next_interval += timedelta(
                    seconds=(
                        next_interval.total_seconds() *
                        self.GRADE_EASY_BONUS_FACTOR
                    ))

            # Early review.
            if self.card.due_at and self._percent_waited() < 1.0:
                # The interval should only be increased by an amount
                # proportionate to the percent of time waited until the
                # due date. This increase will be `interval_delta`.
                interval_delta = next_interval - current_interval
                factor = self._adjustment_curve(self._percent_waited())
                interval_delta = _multiply_timedelta(
                    interval_delta, factor)

                # Reset `next_interval` using the new delta.
                next_interval = current_interval + interval_delta
        return next_interval

    def _next_ease_factor(self):
        next_ease_factor = (
            self.card.ease_factor +
            self.EASE_FACTOR_MODIFIERS[self.grade]
        )

        # Early review?
        if self.card.due_at and self._percent_waited() < 1.0:
            # Only increase EF proportionate to the percent of the
            # repetition which elapsed.
            delta = next_ease_factor - self.card.ease_factor
            factor = self._adjustment_curve(self._percent_waited())
            delta *= factor

            # Reset EF using the new delta.
            next_ease_factor = self.card.ease_factor + delta

        # Enforce a minimum EF
        next_ease_factor = max(next_ease_factor, self.MINIMUM_EASE_FACTOR)

        return next_ease_factor

    def _next_due_at(self):
        '''
        Returns the new due date for this card.
        '''
        next_ease_factor = self._next_ease_factor()
        next_interval = self._next_interval()
        next_due_at = self.reviewed_at + next_interval
        return next_due_at


    def _time_waited(self):
        '''
        The time elapsed since last review.
        '''
        return self.reviewed_at - self.card.last_reviewed_at

    @lru_cache(maxsize=None)
    def _percent_waited(self):
        '''
        Returns the percent of the last repetition the user waited before
        reviewing.

        So if the next due date was in 5 days, and the user waited just
        3 days before reviewing again, this would return .6.

        Assumes the last review was successful. This method may be
        overriden for new and failed cards.

        Could be considered early (< 1.0) for 2 reasons:
            1. Reviewed before its due date.
            2. Sibling card was reviewed too recently, regardless of
               due dates.

        Determining "too recently" for #2 relies on the amount decided on
        for simultaneously due cards to be delayed for being siblings.

        See the card's `calculated_interval` docstring for info on the
        denominator here.
        '''
        from .cards import Card

        denominator = self.card.calculated_interval()

        # Was this reviewed too soon after a sibling? How early?
        # If not too early, still factor the delay into our return value.
        try:
            sibling = self.card.siblings.latest('last_reviewed_at')
            if sibling.last_reviewed_at:
                difference = (self.card.due_at
                              - sibling.last_reviewed_at)

                if abs(difference) <= self.card.sibling_spacing():
                    denominator += self.card.sibling_spacing()
        except Card.DoesNotExist:
            pass

        return (timedelta_to_float(self._time_waited())
                / timedelta_to_float(denominator))

    def _adjustment_curve(self, percentage):
        '''
        Adjusts `percentage` accordingly:
        where percentage is between 0 and 1,
        curve mid_point is between 0 and 1,
        the x value at which the curve slope rate of change is 0.

        The curve begins at the trough of a cosine wave, and ends at
        the next peak, roughly. Its purpose is to make reviews done near
        enough to the due date to count as pretty much having waited the
        full amount of time, as well as the inverse of this.
        '''
        if percentage > 1.0:
            raise ValueError('Does not work with percentages > 1.0')

        #TODO-OLD refactor magic numbers
        # ((1-cos(.88*pi*.79))/2)/((1-cos(pi*.79))/2)
        upper_x_bound = .79 #midpoint is around .88
        max_value = ((1 - cos(pi * upper_x_bound)))
        return ((1 - cos(percentage * pi * upper_x_bound))) / max_value

    def _fuzz_interval(self, interval):
        '''Returns a fuzzed interval.'''
        # Conservatively favors shorter intervals.
        fuzz = interval * random.triangular(
            -INTERVAL_FUZZ_MAX,
             INTERVAL_FUZZ_MAX,
            (-INTERVAL_FUZZ_MAX) / 4.5)

        # Fuzz less for early reviews.
        if self._is_early_review():
            #TODO-OLD refactor / DRY all these early review calculations
            if self.last_reviewed_at:
                last_effective_interval = timedelta_to_float(
                    self.due_at - self.last_reviewed_at)
                if (is_early_review_due_to_sibling
                    and last_reviewed_sibling.last_reviewed_at
                        > self.last_reviewed_at):
                    last_effectively_reviewed_at = \
                        last_reviewed_sibling.last_reviewed_at
                else:
                    last_effectively_reviewed_at = self.last_reviewed_at

                percentage_waited = (
                    timedelta_to_float(
                        reviewed_at
                        - last_effectively_reviewed_at)
                    / last_effective_interval)
            # New card.
            else:
                percentage_waited = percentage_waited_for_sibling
            #print 'fuzz was to be: ' + str(fuzz)
            fuzz *= self._adjustment_curve(percentage_waited)
            #print 'adjusted fuzz: ' + str(fuzz)
        next_interval += timedelta(days=fuzz)
        #print 'and after fuzz: ' + str(next_interval)

    def fuzz(self, next_repetition):
        ''' Fuzzes the interval and due date for a repetition. Idempotent. '''
        if next_repetition.fuzzed:
            return
        next_repetition.fuzzed = True


class YoungCardAlgo(RepetitionAlgo):
    # Max interval bonus factor
    INTERVAL_BONUS_FACTOR_CAP = 3.0

    def _is_being_learned(self):
        '''
        Returns whether this card is still being learned.

        This is something that has to be estimated somehow. For now we
        define this as having an interval less than the minimum preset
        interval for "Easy" grades.
        '''
        return (self.card.interval
                < initial_interval(self.card.fact.deck, GRADE_EASY))

    def _next_interval(self, failure_interval=timedelta()):
        return super(YoungCardAlgo, self)._next_interval(
            failure_interval=self.YOUNG_FAILURE_INTERVAL)

    def _next_ease_factor(self):
        # Don't update if card is still very young, i.e. still being
        # learned, unless graded "Easy"
        if self._is_being_learned() and self.grade != GRADE_EASY:
            return self.card.ease_factor

        # Only make the ease factor harder if the last review grade was
        # better than this review.
        #TODO-OLD implement this?

        return super(YoungCardAlgo, self)._next_ease_factor()


class MatureCardAlgo(RepetitionAlgo):
    def _next_interval(self, failure_interval=timedelta()):
        return super(MatureCardAlgo, self)._next_interval(
            failure_interval=self.MATURE_FAILURE_INTERVAL)


class NewCardAlgo(RepetitionAlgo):
    def _next_interval(self, failure_interval=timedelta()):
        #FIXME, do_fuzz=do_fuzz)
        interval = initial_interval(self.card.fact.deck, self.grade)

        #TODO-OLD Lessen interval if reviewed too soon after a sibling card.
        return interval

    def _next_ease_factor(self):
        #TODO-OLD lower it if graded soon after a sibling, but lower than the
        # sibling's grade.
        #TODO-OLD don't add modifier if rated well soon after a sibling
        # Default to the average for this deck
        ease_factor = (self.card.deck.average_ease_factor()
                       + self.EASE_FACTOR_MODIFIERS[self.grade])

        # Boost it only for "Easy" grades.
        if self.grade == GRADE_EASY:
            ease_factor += self.EASE_FACTOR_MODIFIERS[self.grade]

        return ease_factor


class FailedCardAlgo(RepetitionAlgo):
    '''
    For cards that were failed in their last repetition.

    The current repetition whose grade this algorithm accounts for
    may have failed or succeeded - this takes the new grade into account.
    '''
    # If the user runs out of due cards, failed cards will come up
    # regardless of their due time. However, they will come up this
    # amount of time after being failed if other cards are still due.
    #
    # So this is a maximum possible delay, in other words (as long as the
    # user is still reviewing, of course).
    #SOFT_DELAY = timedelta(60) # minutes
    # This is just the deck's unknown interval

    def _next_interval(self, failure_interval=timedelta()):
        #FIXME, do_fuzz=do_fuzz)
        interval = initial_interval(self.card.fact.deck, self.grade)

        #TODO-OLD lessen effect if reviewed successfully very soon after a
        # failed review.

        return interval

    def _next_ease_factor(self):
        '''
        Won't lower the EF since the last review was a failure. This is to
        prevent the EF from dropping too rapidly. It only lowers the first
        time the card is failed after being new or after successful
        reviews (when the card isn't considered a Failed Card).
        '''
        ease_factor = super(FailedCardAlgo, self)._next_ease_factor()

        if ease_factor < self.card.ease_factor:
            return self.card.ease_factor

        return ease_factor


class NextRepetition:
    '''
    Contains the next scheduled repetition for the associated card.
    '''
    def __init__(self, card, interval, ease_factor, due_at):
        self.card = card
        self.interval = interval
        self.ease_factor = ease_factor
        self.due_at = due_at
        self.fuzzed = False
