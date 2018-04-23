import random
from datetime import timedelta

from .constants import (
    GRADE_EASY,
    GRADE_GOOD,
    GRADE_HARD,
    GRADE_NONE,
)

DEFAULT_INTERVALS = {
    GRADE_NONE: (20.0/(24.0*60.0), 25.0/(24.0*60.0)),
    #cards.GRADE_mature_unknown': (0.333, 0.333),
    GRADE_HARD: (0.333, 0.5),
    GRADE_GOOD: (3.0, 5.0),
    GRADE_EASY: (7.0, 9.0),
}


def _generate_interval(min_duration, max_duration):
    #TODO-OLD favor (random.triangular) conservatism
    return timedelta(days=random.uniform(min_duration, max_duration))


def initial_interval(deck, grade, do_fuzz=True):
    '''
    Generates an initial interval duration for a new card that's been reviewed.
    '''
    min_, max_ = DEFAULT_INTERVALS[grade]

    if do_fuzz:
        return _generate_interval(min_, max_)
    return timedelta(days=((min_ + max_) / 2.0))
