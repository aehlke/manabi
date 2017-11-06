from datetime import datetime, timedelta

from django.conf import settings
from django.test import Client
from freezegun import freeze_time
from pytz import timezone

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

    def _review_card(self):
        next_cards = self.api.next_cards_for_review(self.user)['cards']
        next_card = next_cards[0]
        return self.api.review_card(self.user, next_card, GRADE_EASY)

    def test_cards_reviewed(self):
        review_began_at = datetime.utcnow()

        results = self.api.review_results(self.user, review_began_at)
        self.assertEqual(results['cards_reviewed'], 0)

        self._review_card()

        results = self.api.review_results(self.user, review_began_at)
        self.assertEqual(results['cards_reviewed'], 1)

    def test_current_streak(self):
        est = timezone('US/Eastern')
        start_date = est.localize(
            datetime(2017, 11, 5, settings.START_OF_DAY + 10))

        with freeze_time(start_date) as frozen_datetime:
            results = self.api.review_results(self.user, datetime.utcnow())
            self.assertEqual(results['current_daily_streak'], 0)

            for _ in range(2):
                self._review_card()
                results = self.api.review_results(self.user, datetime.utcnow())
                self.assertEqual(results['current_daily_streak'], 1)

            frozen_datetime.tick(delta=timedelta(days=1))
            results = self.api.review_results(self.user, datetime.utcnow())
            self.assertEqual(results['current_daily_streak'], 0)

            self._review_card()
            results = self.api.review_results(self.user, datetime.utcnow())
            self.assertEqual(results['current_daily_streak'], 2)

    def test_days_reviewed_by_week(self):
        est = timezone('US/Eastern')
        # A Sunday.
        start_date = est.localize(
            datetime(2017, 11, 5, settings.START_OF_DAY + 1))

        with freeze_time(start_date) as frozen_datetime:
            week = self.api.review_results(
                self.user, datetime.utcnow())['days_reviewed_by_week'][-1]
            self.assertEqual(week['week'], '11/5')
            self.assertEqual(week['days_reviewed'], 0)

            for days in range(1, 6):
                self._review_card()

                week = self.api.review_results(
                    self.user, datetime.utcnow())['days_reviewed_by_week'][-1]
                self.assertEqual(week['week'], '11/5')
                self.assertEqual(week['days_reviewed'], days)

                frozen_datetime.tick(delta=timedelta(days=1))
