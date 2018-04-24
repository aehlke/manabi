from manabi.apps.flashcards.models.constants import (
    TRIAL_DAILY_REVIEW_CAP,
    DEFAULT_TIME_ZONE,
)
from manabi.apps.flashcards.models import CardHistory
from manabi.apps.subscriptions.models import user_is_active_subscriber


def cards_remaining_in_daily_trial(user, time_zone=None):
    '''
    Returns how many cards to review today the user has left in their trial.

    If the user has an active subscription, returns None.
    '''
    if user.is_anonymous:
        raise ValueError("Requires authenticated user.")

    if user.username in ['alextest']:
        return None

    if user_is_active_subscriber(user):
        return None

    reviewed_today_count = (
        CardHistory.objects
        .of_day_for_user(user, time_zone or DEFAULT_TIME_ZONE)
        .count()
    )

    return max(0, TRIAL_DAILY_REVIEW_CAP - reviewed_today_count)
