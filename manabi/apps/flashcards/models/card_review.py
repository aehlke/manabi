from datetime import datetime, timedelta

from humanize.time import naturaldelta


class CardReview:
    def __init__(self, card, grade):
        self.card = card
        self.grade = grade
        self._review_applied = False

    def apply_review(self):
        self.card.review(self.grade)
        self._review_applied = True

    def next_due_at(self):
        if not self._review_applied:
            raise Exception("Must first apply the review.")
        return self.card.due_at

    def humanized_next_due_in(self):
        '''
        Can be appended to the prefix "Next review ...".
        '''
        if not self._review_applied:
            raise Exception("Must first apply the review.")

        due_in = self.card.due_at - datetime.utcnow()
        if due_in < timedelta(minutes=1):
            return "in less than a minute"
        return "in {}".format(naturaldelta(due_in, months=True))
