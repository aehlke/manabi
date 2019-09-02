# -*- coding: utf-8 -*-

import itertools
import json
import urllib.request, urllib.parse, urllib.error
from datetime import datetime, timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings

from manabi.apps.featured_decks.models import FeaturedDeck
from manabi.apps.flashcards.models import (
    DeckCollection,
    Deck,
    Fact,
    Card,
)
from manabi.apps.flashcards.models.constants import (
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY,
    DEFAULT_EASE_FACTOR,
)
from manabi.apps.flashcards.models.new_cards_limit import NewCardsLimit
from manabi.test_helpers import (
    ManabiTestCase,
    create_sample_data,
    create_user,
    create_deck_collection,
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

    def test_deck_deletion_marks_cards_as_inactive(self):
        sample_deck = Deck.objects.get(id=self.api.decks(self.user)[0]['id'])
        self.assertTrue(sample_deck.active)

        self.api.delete(
            '/api/flashcards/decks/{}/'.format(sample_deck.id),
            user=self.user,
        )
        self.assertFalse(Deck.objects.get(id=sample_deck.id).active)

        print(sample_deck.card_set.values_list('active', flat=True))
        self.assertFalse(any(
            sample_deck.card_set.values_list('active', flat=True)))


class ReviewsAPITest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        self.facts = create_sample_data(facts=12, user=self.user)

    def test_next_cards_for_review(self):
        self.assertTrue(self.api.next_cards_for_review(self.user))

    def test_next_cards_for_review_includes_interstitial_with_prompt(self):
        next_cards_for_review = self.api.next_cards_for_review(self.user)
        interstitial = next_cards_for_review['interstitial']
        review_availabilities = interstitial['review_availabilities']
        # FIXME self.assertTrue(review_availabilities['trial_prompt'])

    def test_manabi_reader_cards_for_review(self):
        reader_fact = self.facts[0]
        reader_fact.jmdict_id = 123
        reader_fact.save()

        next_cards_for_review = (
            self.api.manabi_reader_next_cards_for_review(
                self.user, [123], []))

        cards = next_cards_for_review['cards']
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]['expression'], reader_fact.expression)

    def test_review_cards(self):
        count = 0
        while True:
            cards = self.next_cards_for_review(self.user)
            if not cards:
                break
            count += 1
            card_ids = [card['id'] for card in cards]

            next_cards = self.api.next_cards_for_review(self.user)['cards']
            for card in next_cards:
                self.assertFalse(card['id'] in card_ids)
        self.assertTrue(count)

    def test_late_review(self):
        grades = itertools.cycle(
            [GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY])
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
            card_review = self.api.review_card(
                self.user, card['id'], GRADE_GOOD)

    def test_new_cards_appear_after_due_cards(self):
        NEW_COUNT = 2

        # Review all but last NEW_COUNT
        cards = self.api.next_cards_for_review(self.user)['cards']
        self.assertTrue(NEW_COUNT < len(cards))
        for card in cards[:-NEW_COUNT]:
            self.api.review_card(self.user, card['id'], GRADE_GOOD)

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
        card_review = self.api.review_card(
            self.user, next_card['id'], GRADE_EASY)
        self.assertNotEqual(card_review['next_due_at'], due_at_before_review)

        undone_card = self.api.undo_review(self.user)
        self.assertEqual(undone_card['due_at'], due_at_before_review)
        self.assertEqual(
            Card.objects.get(id=next_card['id']).due_at,
            due_at_before_review)

    def test_review_availabilities(self):
        self.api.review_availabilities(self.user)

    def test_review_availabilities_for_manabi_reader(self):
        review_availabilities = self.api.review_availabilities(
            self.user,
            is_for_manabi_reader=True,
            jmdict_ids=[],
        )
        self.assertEqual(review_availabilities['next_new_cards_count'], 0)

        reader_fact = self.facts[0]
        reader_fact.jmdict_id = 123
        reader_fact.save()

        review_availabilities = self.api.review_availabilities(
            self.user,
            is_for_manabi_reader=True,
            jmdict_ids=[reader_fact.jmdict_id],
        )
        self.assertEqual(review_availabilities['next_new_cards_count'], 1)


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


class SharedDecksTest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        create_sample_data(facts=2, user=self.user)

        self.shared_deck = Deck.objects.filter(owner=self.user).first()
        self.shared_deck.share()

        self.subscriber = create_user()
        self.api.add_shared_deck(self.shared_deck, self.subscriber)

    def test_shared_decks_by_author(self):
        decks = self.api.shared_decks(of_user=self.user)
        self.assertEqual(len(decks), 1)
        self.assertEqual(decks[0]['owner']['username'], self.user.username)

    def test_shared_decks_by_subscriber(self):
        decks = self.api.shared_decks(of_user=self.subscriber)
        self.assertEqual(len(decks), 1)
        self.assertEqual(decks[0]['owner']['username'], self.user.username)

    def test_featured_decks(self):
        FeaturedDeck.objects.create(deck=self.shared_deck)

        featured_decks = self.api.suggested_shared_decks()['featured_decks']
        self.assertTrue(len(featured_decks), 1)
        self.assertEqual(featured_decks[0]['id'], self.shared_deck.id)

    def test_deck_subscribers(self):
        subscribers = self.api.shared_deck_subscribers(self.shared_deck)
        print(subscribers)
        self.assertEqual(len(subscribers), 1)

    def test_subscribed_shared_deck_has_viewer_synchronized_deck_field(self):
        featured_deck = create_deck()
        featured_deck.share()
        FeaturedDeck.objects.create(deck=featured_deck)

        featured_decks = self.api.suggested_shared_decks(
            viewer=self.subscriber)['featured_decks']
        self.assertIsNone(featured_decks[0]['viewer_synchronized_deck'])

        subscribed_deck = self.api.add_shared_deck(
            featured_deck, self.subscriber)

        featured_decks = self.api.suggested_shared_decks(
            viewer=self.subscriber)['featured_decks']
        self.assertIsNotNone(
            featured_decks[0]['viewer_synchronized_deck']['id'])
        self.assertEqual(
            featured_decks[0]['viewer_synchronized_deck']['id'],
            subscribed_deck['id'],
        )

    def test_card_counts_in_suggested_decks(self):
        FeaturedDeck.objects.create(
            deck=self.shared_deck,
        )
        featured_decks = self.api.suggested_shared_decks()['featured_decks']
        self.assertEqual(
            featured_decks[0]['card_count'],
            self.shared_deck.refresh_card_count())
        self.assertEqual(
            Deck.objects.filter(
                id__in=[self.shared_deck.id],
            ).card_counts()[self.shared_deck.id],
            self.shared_deck.refresh_card_count())

    def test_featured_decks_tree(self):
        collection = create_deck_collection()
        self.shared_deck.collection = collection
        self.shared_deck.save(update_fields=['collection'])
        FeaturedDeck.objects.create(
            deck_collection=collection,
        )
        tree = self.api.suggested_shared_decks()['featured_decks_tree']
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['deck_collection']['id'], collection.id)


    # def test_featured_decks_queries_do_not_increase_with_featured_count(self):
    #     QUERY_COUNT = 18
    #
    #     FeaturedDeck.objects.create(
    #         deck=self.shared_deck,
    #     )
    #     with self.assertNumQueries(QUERY_COUNT):
    #         self.api.suggested_shared_decks()
    #     with self.assertNumQueries(QUERY_COUNT):
    #         self.api.suggested_shared_decks()
    #
    #     for _ in range(4):
    #         create_sample_data(facts=2)
    #     for deck in Deck.objects.filter(
    #             shared=False, synchronized_with__isnull=True):
    #         deck.share()
    #         FeaturedDeck.objects.create(
    #             deck=deck,
    #         )
    #     with self.assertNumQueries(QUERY_COUNT):
    #         self.api.suggested_shared_decks()


class DeckTest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        create_sample_data(facts=6, user=self.user)
        self.deck = Deck.objects.all().last()

    def test_average_ease_factor_on_new_deck_is_default(self):
        self.assertEqual(self.deck.average_ease_factor(), DEFAULT_EASE_FACTOR)

    def test_deletion_marks_cards_inactive(self):
        sample_card = self.deck.card_set.first()
        self.assertTrue(sample_card.active)

        self.deck.delete()
        sample_card = Card.objects.get(pk=sample_card.pk)
        self.assertFalse(sample_card.active)

    def test_denormalized_card_count(self):
        deck = Deck.objects.filter(owner=self.user)[0]

        def assert_card_count():
            actual_count = Card.objects.of_deck(deck).available().count()
            self.assertEqual(
                actual_count,
                Deck.objects.get(id=deck.id).card_count)
            return actual_count

        original_count = assert_card_count()

        fact_to_suspend = deck.facts.filter(active=True, suspended=False)[0]
        fact_card_count = fact_to_suspend.card_set.count()
        self.assertTrue(fact_card_count > 0)

        self.assertFalse(Fact.objects.get(id=fact_to_suspend.id).suspended)
        self.api.suspend_fact(self.user, fact_to_suspend.id)
        self.assertTrue(Fact.objects.get(id=fact_to_suspend.id).suspended)
        new_count = assert_card_count()
        self.assertEqual(original_count - fact_card_count, new_count)

    def test_reviewed_subscriber_deck_isnt_destroyed_when_synced_deck_is(self):
        subscriber = create_user()
        self.deck.share()
        subscriber_deck = self.deck.subscribe(subscriber)

        self.assertFalse(subscriber_deck.suspended)
        self.assertTrue(subscriber_deck.active)

        self.deck.is_suspended = True
        self.deck.save()
        self.assertFalse(Deck.objects.get(id=subscriber_deck.id).suspended)

        self.deck.suspended = False
        self.deck.save()
        self.deck.delete()
        subscriber_deck = Deck.objects.get(id=subscriber_deck.id)
        self.assertFalse(subscriber_deck.suspended)
        self.assertTrue(subscriber_deck.active)


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
            self.assertTrue(Card.objects.get(id=card['id']).is_new)
            self.api.review_card(self.user, card['id'], GRADE_GOOD)
            self.assertEqual(idx + 1, self._get_limit().learned_today_count)

    def test_other_user_reviews_dont_conflict(self):
        cards = self.api.next_cards_for_review(self.user)['cards']
        self.api.review_card(self.user, cards[0]['id'], GRADE_GOOD)

        self.assertEqual(
            0, self._get_limit(user=create_user()).learned_today_count)


class FactsTest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        create_sample_data(facts=4, user=self.user)

    def _get_facts(self):
        return Fact.objects.filter(deck__owner=self.user)

    def test_suspending_matching_facts_by_reading(self):
        for fact in self._get_facts():
            self.assertFalse(fact.suspended)

        fact_to_suspend = self._get_facts()[0]
        self.api.suspend_facts(self.user, fact_to_suspend.reading)
        for fact in self._get_facts():
            self.assertEqual(fact.suspended, fact.id == fact_to_suspend.id)

    def test_suspending_matching_facts_by_jmdict_id(self):
        for fact in self._get_facts():
            self.assertFalse(fact.suspended)

        fact_to_suspend = self._get_facts()[0]
        fact_to_suspend.jmdict_id = 123
        fact_to_suspend.save()

        self.api.suspend_facts(
            self.user, 'reading that will not match', jmdict_id=123)
        for fact in self._get_facts():
            self.assertEqual(fact.suspended, fact.id == fact_to_suspend.id)

    def test_fact_deletion(self):
        fact_to_delete = self._get_facts()[0]

        self.assertTrue(fact_to_delete.active)
        self.assertTrue(
            any(fact['id'] == fact_to_delete.id
                for fact in self.api.facts(self.user)))
        self.assertTrue(
            any(fact['id'] == fact_to_delete.id
                for fact
                in self.api.facts(self.user, deck=fact_to_delete.deck)))

        self.api.delete(
            f'/api/flashcards/facts/{fact_to_delete.id}/',
            user=self.user,
        )
        self.assertFalse(Fact.objects.get(id=fact_to_delete.id).active)

        # Deleted fact doesn't show up in API requests.
        self.assertFalse(
            any(fact['id'] == fact_to_delete.id
                for fact in self.api.facts(self.user)))
        self.assertFalse(
            any(fact['id'] == fact_to_delete.id
                for fact
                in self.api.facts(self.user, deck=fact_to_delete.deck)))
        self.assertTrue(
            all(fact['active'] for fact in self.api.facts(user=self.user)))



class ManabiReaderFactsTest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()

    def test_valid_creation(self):
        fact = self.post(
            '/api/flashcards/manabi_reader_facts/',
            {
                'expression': '食べる',
                'reading': 'たべる',
                'meaning': 'To eat',
                'active_card_templates': ['recognition'],
            },
            user=self.user,
        ).json()
        self.assertEqual(
            Deck.objects.get(id=fact['deck']).name, 'Manabi Reader')

    def test_valid_creation_with_jmdict_id(self):
        jmdict_id = 1419270
        fact = self.post(
            '/api/flashcards/manabi_reader_facts/',
            {
                'expression': '団体',
                'reading': '｜団《だん》｜体《たい》',
                'meaning': 'Organization, organisation, association',
                'active_card_templates': ['recognition'],
                'example_sentence': 'デモを行った団体によると、１０３万人が参加しました。',
                'jmdict_id': jmdict_id,
            },
            user=self.user,
        ).json()
        self.assertEqual(Fact.objects.last().jmdict_id, jmdict_id)

    def test_multiple_from_same_source(self):
        for suffix in ['1', '2']:
            resp = self.post(
                '/api/flashcards/manabi_reader_facts/',
                {
                    'expression': '食べる' + suffix,
                    'reading': 'たべる',
                    'meaning': 'To eat',
                    'active_card_templates': ['recognition'],
                    'reader_source': {
                        'source_url': 'http://foo.example/bar',
                        'thumbnail_url': 'http://foo.example/baz.jpg',
                        'title': 'Example title' + suffix,
                    },
                },
                user=self.user,
            )
            self.assertEqual(resp.status_code, 201)

    def test_adding_same_word_twice_updates_existing_one(self):
        for idx in range(2):
            example_sentence = f'パンを食べる {idx}'
            fact = self.post(
                '/api/flashcards/manabi_reader_facts/',
                {
                    'expression': '食べる',
                    'reading': 'たべる',
                    'meaning': 'To eat',
                    'example_sentence': example_sentence,
                    'active_card_templates': ['recognition'],
                },
                user=self.user,
            ).json()

            self.assertEqual(
                Deck.objects.get(id=fact['deck']).facts.count(), 1)
            self.assertEqual(
                Deck.objects.get(
                    id=fact['deck']).facts.first().example_sentence,
                    example_sentence)
