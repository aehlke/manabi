from datetime import datetime

from django.test import Client

from manabi.apps.flashcards.models.constants import (
    GRADE_EASY,
)
from manabi.test_helpers import (
    ManabiTestCase,
    create_sample_data,
    create_user,
    create_deck_collection,
    create_deck,
)


class ReviewResultsAPITest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        self.facts = create_sample_data(facts=3, user=self.user)

    def test_review_results(self):
        review_began_at = datetime.utcnow()

        results = self.api.review_results(self.user, review_began_at)
        self.assertEqual(results['cards_reviewed'], 0)

        next_cards = self.api.next_cards_for_review(self.user)['cards']
        next_card = next_cards[0]
        card_review = self.api.review_card(self.user, next_card, GRADE_EASY)

        results = self.api.review_results(self.user, review_began_at)
        self.assertEqual(results['cards_reviewed'], 1)
