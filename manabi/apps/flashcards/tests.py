# -*- coding: utf-8 -*-

import itertools
import json
import urllib
from datetime import datetime, timedelta

from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.conf import settings

from manabi.apps.flashcards.models import Deck, Fact, Card
from manabi.apps.flashcards.models.constants import (
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY,
    DEFAULT_EASE_FACTOR,
)
from manabi.apps.flashcards.models.new_cards_limit import NewCardsLimit
from manabi.test_helpers import (
    ManabiTestCase,
    create_sample_data,
    create_user,
    create_deck,
)


class DecksAPITest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        create_sample_data(facts=1, user=self.user)

    def test_deck_list(self):
        self.assertEqual(1, Deck.objects.filter(owner=self.user).count())
        decks = self.api.decks(self.user)
        self.assertEqual(1, len(decks))


class ReviewsAPITest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        self.facts = create_sample_data(facts=10, user=self.user)

    def test_next_cards_for_review(self):
        self.assertTrue(self.api.next_cards_for_review(self.user))

    def test_review_cards(self):
        count = 0
        while True:
            cards = self.next_cards_for_review(self.user)
            if not cards:
                break
            count += 1
            card_ids = map(lambda card: card['id'], cards)

            next_cards = self.api.next_cards_for_review(self.user)['cards']
            for card in next_cards:
                self.assertFalse(card['id'] in card_ids)
        self.assertTrue(count)

    def test_late_review(self):
        grades = itertools.cycle([GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY])
        for fact in self.facts:
            for grade, card in zip(grades, fact.card_set.all()):
                card.due_at = datetime.utcnow() - timedelta(days=1)
                card.last_review_grade = grade
                card.last_reviewed_at = datetime.utcnow() - timedelta(days=2)
                if grade == GRADE_NONE:
                    card.last_failed_at = card.last_reviewed_at
                card.interval = timedelta(hours=4)
                card.ease_factor = 1.1
                card.template = 0
                card.save()

        for card in self.next_cards_for_review(self.user):
            card_review = self.api.review_card(self.user, card, GRADE_GOOD)

    def test_new_cards_appear_after_due_cards(self):
        NEW_COUNT = 2

        # Review all but last NEW_COUNT
        cards = self.api.next_cards_for_review(self.user)['cards']
        self.assertTrue(NEW_COUNT < len(cards))
        for card in cards[:-NEW_COUNT]:
            self.api.review_card(self.user, card, GRADE_GOOD)

        # Make sure there are still new cards at end.
        cards = self.api.next_cards_for_review(self.user)['cards']
        new_cards_to_learn_count = sum(
            1 for card in cards if card['is_new']
        )
        self.assertTrue(new_cards_to_learn_count >= NEW_COUNT)

    def test_undo_review(self):
        next_cards = self.api.next_cards_for_review(self.user)['cards']
        next_card = next_cards[0]

        due_at_before_review = next_card['due_at']
        card_review = self.api.review_card(self.user, next_card, GRADE_EASY)
        self.assertNotEqual(card_review['next_due_at'], due_at_before_review)

        undone_card = self.api.undo_review(self.user)
        self.assertEqual(undone_card['due_at'], due_at_before_review)
        self.assertEqual(
            Card.objects.get(id=next_card['id']).due_at,
            due_at_before_review)

    def test_review_availabilities(self):
        pass


class SynchronizationTest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        create_sample_data(facts=30, user=self.user)

        self.shared_deck = Deck.objects.filter(owner=self.user).first()
        self.shared_deck.share()

        self.subscriber = create_user()

    def _subscribe(self, deck):
        deck_id = self.api.add_shared_deck(deck, self.subscriber)['id']
        return Deck.objects.get(id=deck_id)

    def test_deck_subscription(self):
        subscribed_deck = self._subscribe(self.shared_deck)
        self.assertEqual(
            subscribed_deck.synchronized_with_id,
            self.shared_deck.id,
        )

    def test_moving_shared_fact_to_another_shared_deck(self):
        subscribed_deck = self._subscribe(self.shared_deck)

        target_deck = create_deck(user=self.user)
        target_deck.share()
        target_subscribed_deck = self._subscribe(target_deck)

        shared_fact = self.shared_deck.facts.first()

        # Subscribed deck got synchronized fact.
        self.assertEqual(
            subscribed_deck.facts.count(),
            self.shared_deck.facts.count(),
        )
        subscribed_deck.facts.get(synchronized_with_id=shared_fact.id)

        moved_fact = self.api.move_fact_to_deck(
            shared_fact, target_deck, self.user)

        with self.assertRaises(Fact.DoesNotExist):
            self.shared_deck.facts.get(id=moved_fact['id'])
        with self.assertRaises(Fact.DoesNotExist):
            subscribed_deck.facts.get(
                synchronized_with_id=moved_fact['id'])

        # Deck the fact was moved to has the fact.
        target_deck.facts.get(id=moved_fact['id'])

        # Subscribed deck of deck the fact was moved to has the fact.
        target_subscribed_deck.facts.get(
            synchronized_with_id=moved_fact['id'],
        )


class DeckTest(ManabiTestCase):
    def after_setUp(self):
        create_sample_data(facts=30)
        self.deck = Deck.objects.all().last()

    def test_average_ease_factor_on_new_deck_is_default(self):
        self.assertEqual(self.deck.average_ease_factor(), DEFAULT_EASE_FACTOR)


class NewCardsLimitTest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        create_sample_data(facts=4, user=self.user)

    def _get_limit(self, user=None):
        return NewCardsLimit(user or self.user)

    def test_learned_today_count_begins_at_zero(self):
        self.assertEqual(0, self._get_limit().learned_today_count)

    def test_learned_today_count_increases_with_review(self):
        cards = self.api.next_cards_for_review(self.user)['cards']
        for idx, card in enumerate(cards):
            self.api.review_card(self.user, card, GRADE_GOOD)
            self.assertEqual(idx + 1, self._get_limit().learned_today_count)

    def test_other_user_reviews_dont_conflict(self):
        cards = self.api.next_cards_for_review(self.user)['cards']
        self.api.review_card(self.user, cards[0], GRADE_GOOD)

        self.assertEqual(0, self._get_limit(user=create_user()).learned_today_count)
