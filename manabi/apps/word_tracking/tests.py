from manabi.apps.flashcards.models.constants import (
    GRADE_GOOD,
)
from manabi.apps.flashcards.models import (
    Deck,
    Fact,
)
from manabi.test_helpers import (
    ManabiTestCase,
    create_sample_data,
    create_user,
)


class WordTrackingAPITest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        create_sample_data(facts=3, user=self.user)

        self.fact_without_jmdict_id = Fact.objects.filter(
            deck__owner=self.user).first()

        self.jmdict_fact = Fact.objects.filter(
            deck__owner=self.user).last()
        self.jmdict_fact.jmdict_id = 1011880
        self.jmdict_fact.save()

    def test_zero_cards(self):
        for deck in Deck.objects.filter(owner=self.user):
            deck.delete()
        tracked_words = self.api.tracked_words(self.user)
        for field in [
            'learning_jmdict_ids',
            'known_jmdict_ids',
            'learning_words_without_jmdict_ids',
            'known_words_without_jmdict_ids'
        ]:
            self.assertEqual(tracked_words[field], [])

    def test_zero_reviews(self):
        tracked_words = self.api.tracked_words(self.user)
        for field in [
            'known_jmdict_ids',
            'known_words_without_jmdict_ids'
        ]:
            self.assertEqual(tracked_words[field], [])

    def test_review_card_with_jmdict_id(self):
        jmdict_card_id = self.jmdict_fact.card_set.first().id
        self.api.review_card(self.user, jmdict_card_id, GRADE_GOOD)

        tracked_words = self.api.tracked_words(self.user)
        self.assertEqual(
            tracked_words['learning_jmdict_ids'], [self.jmdict_fact.jmdict_id])

        self.assertEqual(tracked_words['known_jmdict_ids'], [])

    def test_review_card_without_jmdict_id(self):
        card_id = self.fact_without_jmdict_id.card_set.first().id
        self.api.review_card(self.user, card_id, GRADE_GOOD)

        tracked_words = self.api.tracked_words(self.user)
        self.assertEqual(
            tracked_words['learning_words_without_jmdict_ids'],
            [self.fact_without_jmdict_id.reading])

        self.assertEqual(tracked_words['known_words_without_jmdict_ids'], [])

    def test_no_dupes_across_categories(self):
        card_id = self.fact_without_jmdict_id.card_set.first().id
        self.api.review_card(self.user, card_id, GRADE_GOOD)

        tracked_words = self.api.tracked_words(self.user)

        seen_ids = set()
        for field in [
            'new_jmdict_ids',
            'learning_jmdict_ids',
            'known_jmdict_ids',
        ]:
            print(f"Checking {field}")
            new_items = set(tracked_words[field])
            self.assertEqual(len(new_items & seen_ids), 0)
            seen_ids.update(new_items)

        seen_words = set()
        for field in [
            'new_words_without_jmdict_ids',
            'learning_words_without_jmdict_ids',
            'known_words_without_jmdict_ids',
        ]:
            print(f"Checking {field}")
            new_items = set(tracked_words[field])
            self.assertEqual(len(new_items & seen_words), 0)
            seen_words.update(new_items)
