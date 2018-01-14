from manabi.apps.flashcards.models.constants import TRIAL_DAILY_REVIEW_CAP
from manabi.apps.subscriptions.models import user_is_active_subscriber


def cards_remaining_in_daily_trial(user):
    '''
    Returns how many cards to review today the user has left in their trial.

    If the user has an active subscription, returns None.
    '''
    if user.is_anonymous():
        raise ValueError("Requires authenticated user.")

    if user_is_active_subscriber(user):
        return None

    reviewed_today_count = (
        CardHistory.objects
        .of_day_for_user(self.user, self.time_zone or DEFAULT_TIME_ZONE)
        .count()
    )

    return max(0,
               TRIAL_DAILY_REVIEW_CAP
               - reviewed_today_count
               - self._buffered_cards_count),
