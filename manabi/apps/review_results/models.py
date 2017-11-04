from manabi.apps.flashcards.models import CardHistory


class ReviewResults(object):
    '''
    Results for the last review session.
    '''
    def __init__(self, user, review_began_at):
        self.user = user
        self.review_began_at = review_began_at
        self._card_history = (CardHistory.objects
            .of_user(user)
            .filter(reviewed_at__gte=review_began_at)
        )

    @property
    def cards_reviewed(self):
        return self._card_history.count()
