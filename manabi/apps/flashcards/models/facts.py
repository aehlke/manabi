from datetime import datetime, timedelta
import random

from django.db.models.query import QuerySet
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Q, F
from natto import MeCab

from constants import MAX_NEW_CARD_ORDINAL
from manabi.apps.flashcards.signals import fact_suspended, fact_unsuspended
from manabi.apps.flashcards.models.constants import GRADE_NONE, MIN_CARD_SPACE, CARD_SPACE_FACTOR
from manabi.apps.flashcards.models.synchronization import copy_facts_to_subscribers


#TODO-OLD
# separate the cards of this fact initially
# not used for child fact types (?)
#min_card_space = models.FloatField(default=seconds_to_days(600),
#        help_text='Duration expressed in (partial) days.')
#TODO-OLD
# minimal interval multiplier between two cards of the same fact
#space_factor = models.FloatField(default=.1)


class FactQuerySet(QuerySet):
    def deck_facts(self, deck):
        return self.filter(deck=deck)

    def buried(self, user, review_time=None, excluded_card_ids=[]):
        '''
        Facts with cards buried due to siblings.
        '''
        if review_time is None:
            review_time = datetime.utcnow()

        return self.filter(
            Q(card__deck__owner=user) & (
                # Sibling was reviewed too recently.
                | (
                    Q(card__last_reviewed_at__gte=(
                        review_time - MIN_CARD_SPACE))
                    & Q(card__last_reviewed_at__gte=(
                        review_time - F('card__interval') * CARD_SPACE_FACTOR))
                )
                # Sibling is currently in the client-side review queue.
                | Q(card__id__in=excluded_card_ids)
                # Sibling is failed. (Either sibling's due, or it's shown before new cards.)
                | Q(card__last_review_grade=GRADE_NONE)
            )
        )


def _card_template_id_to_string(card_template_id):
    from manabi.apps.flashcards.models import (
        PRODUCTION, RECOGNITION, KANJI_READING, KANJI_WRITING)

    return {
        PRODUCTION: 'production',
        RECOGNITION: 'recognition',
        KANJI_READING: 'kanji_reading',
        KANJI_WRITING: 'kanji_writing',
    }[card_template_id]


def _card_template_string_to_id(card_template):
    from manabi.apps.flashcards.models import (
        PRODUCTION, RECOGNITION, KANJI_READING, KANJI_WRITING)

    return {
        'production': PRODUCTION,
        'recognition': RECOGNITION,
        'kanji_reading': KANJI_READING,
        'kanji_writing': KANJI_WRITING,
    }[card_template]


class Fact(models.Model):
    objects = FactQuerySet.as_manager()

    deck = models.ForeignKey(
        'flashcards.Deck', db_index=True, related_name='facts')

    synchronized_with = models.ForeignKey(
        'self', null=True, blank=True, related_name='subscriber_facts')
    forked = models.BooleanField(default=False, blank=True)

    new_fact_ordinal = models.PositiveIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True, blank=True)

    expression = models.CharField(max_length=500)
    reading = models.CharField(max_length=1500, blank=True)
    meaning = models.CharField(max_length=1000)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(blank=True, null=True)

    suspended = models.BooleanField(default=False)

    def roll_ordinal(self):
        '''
        Returns whether a new ordinal was given.
        '''
        if self.new_fact_ordinal:
            return False
        self.new_fact_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)
        return True

    def save(self, update_fields=None, *args, **kwargs):
        '''
        Set a random sorting index for new cards.

        Propagates changes down to subscriber facts.
        '''
        self.modified_at = datetime.utcnow()
        also_update_fields = {'modified_at'}

        if self.roll_ordinal():
            also_update_fields.add('new_fact_ordinal')

        if (
            not self.forked and
            (
                update_fields is None or
                set(update_fields) & {'expression', 'reading', 'meaning'}
            ) and
            self.synchronized_with is not None and
            (
                self.synchronized_with.expression != self.expression or
                self.synchronized_with.reading != self.reading or
                self.synchronized_with.meaning != self.meaning
            )
        ):
            self.forked = True
            also_update_fields.add('forked')

        if update_fields is not None:
            update_fields = list(set(update_fields) | also_update_fields)

        is_new = self.pk is None

        super(Fact, self).save(*args, **kwargs)

        if update_fields is None or (
            set(update_fields) & {'expression', 'reading', 'meaning'}
        ):
            self.syncing_subscriber_facts.update(
                expression=self.expression,
                reading=self.reading,
                meaning=self.meaning,
            )

        if is_new and self.deck.shared:
            copy_facts_to_subscribers([self])

    @transaction.atomic
    def delete(self, *args, **kwargs):
        self.active = False
        self.save(update_fields=['active'])

        self.new_syncing_subscriber_facts.update(active=False)
        self.subscriber_facts.clear()

    @property
    def syncing_subscriber_facts(self):
        return self.subscriber_facts.exclude(forked=True)

    @property
    def new_syncing_subscriber_facts(self):
        '''
        "New" as in unreviewed.
        '''
        return self.syncing_subscriber_facts.exclude(
            card__last_reviewed_at__isnull=False)

    @property
    def owner(self):
        return self.deck.owner

    @property
    def card_count(self):
        return self.card_set.filter(active=True).count()

    @property
    def active_card_templates(self):
        from manabi.apps.flashcards.models import PRODUCTION

        template_ids = (
            self.card_set.available().values_list('template', flat=True)
        )

        return {
            _card_template_id_to_string(id_) for id_ in template_ids
        }

    def set_active_card_templates(self, card_templates):
        '''
        Creates or updates associated `Card`s.
        '''
        from manabi.apps.flashcards.models import Card

        template_ids = {
            _card_template_string_to_id(template)
            for template in card_templates
        }

        for activated_card in (
            self.card_set.filter(template__in=template_ids)
        ):
            activated_card.activate()

        for deactivated_card in (
            self.card_set.exclude(template__in=template_ids)
        ):
            deactivated_card.deactivate()

        existing_template_ids = set(self.card_set.values_list(
            'template', flat=True))

        for template_id in template_ids - existing_template_ids:
            Card.objects.create(
                deck=self.deck,
                fact=self,
                template=template_id,
                new_card_ordinal=Card.random_card_ordinal(),
            )

        self._set_active_card_templates_for_subscribers(template_ids)

    @transaction.atomic
    def _set_active_card_templates_for_subscribers(self, template_ids):
        from manabi.apps.flashcards.models import Card

        subscriber_cards = Card.objects.filter(
            fact__in=self.syncing_subscriber_facts,
        )
        new_subscriber_cards = subscriber_cards.filter(
            last_reviewed_at__isnull=True,
        )

        new_subscriber_cards.filter(
            template__in=template_ids,
        ).update(active=True)
        new_subscriber_cards.exclude(
            template__in=template_ids,
        ).update(active=False)

        for template_id in template_ids:
            facts_without_template = self.syncing_subscriber_facts.exclude(
                card__in=subscriber_cards.filter(template=template_id),
            )

            missing_cards = [
                Card(
                    deck_id=deck_id,
                    fact_id=fact_id,
                    template=template_id,
                    new_card_ordinal=Card.random_card_ordinal(),
                )
                for fact_id, deck_id in
                facts_without_template.values_list('id', 'deck_id').iterator()
            ]

            Card.objects.bulk_create(missing_cards)

    @transaction.atomic
    def move_to_deck(self, deck):
        self.new_syncing_subscriber_facts.update(active=False)
        self.subscriber_facts.clear()

        self.deck = deck
        self.synchronized_with = None
        self.save(update_fields=['deck', 'synchronized_with'])

        if self.deck.shared:
            copy_facts_to_subscribers([self])

    @transaction.atomic
    def suspend(self):
        self.card_set.update(suspended=True)
        self.suspended = True
        self.save()
        fact_suspended.send(sender=self, instance=self)

    @transaction.atomic
    def unsuspend(self):
        self.card_set.update(suspended=False)
        self.suspended = False
        self.save()
        fact_unsuspended.send(sender=self, instance=self)

    #TODELETE?
    def all_owner_decks(self):
        '''
        Returns a list of all the decks this object belongs to,
        including subscriber decks.
        '''
        return ([self.deck]
                + [d for d in self.deck.subscriber_decks.filter(active=True)])

    class Meta:
        app_label = 'flashcards'
        unique_together = (('deck', 'synchronized_with'),)

    def __unicode__(self):
        return unicode(self.id)
