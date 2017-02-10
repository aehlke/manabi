import datetime
import random
from urlparse import urljoin

from autoslug import AutoSlugField
from cachecow.decorators import cached_function
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import (
    models,
    transaction,
)
from django.db.models import Avg, Count, Q
from django.db.models.query import QuerySet

from manabi.apps.books.models import Textbook
from manabi.apps.flashcards.cachenamespaces import deck_review_stats_namespace
from manabi.apps.flashcards.models import cards
from manabi.apps.flashcards.models.constants import (
    DEFAULT_EASE_FACTOR,
    LATEST_SHARED_DECKS_LIMIT,
)
from manabi.apps.flashcards.models.synchronization import copy_facts_to_subscribers
from manabi.apps.manabi_redis.models import redis


class DeckQuerySet(QuerySet):
    def of_user(self, user):
        if not user.is_authenticated():
            return self.none()

        return self.filter(owner=user, active=True).order_by('name')

    def shared_decks(self):
        return self.filter(shared=True, active=True)

    def latest_shared_decks(self):
        decks = self.shared_decks().order_by('-created_at')
        return decks[:LATEST_SHARED_DECKS_LIMIT]

    def synchronized_decks(self, user):
        if not user.is_authenticated():
            return self.none()

        return self.filter(owner=user, synchronized_with__isnull=False)

    def shared_decks_owned_or_subcribed_by_user(self, user):
        subscribed_decks = self.filter(
            id__in=Deck.objects.synchronized_decks(user)
            .values_list('synchronized_with_id', flat=True)
        )
        return (
            self.filter(shared=True, owner_id=user.id)
            | subscribed_decks
        )

        # .filter(
        #     Q(owner_id=user.id)
        #     | Q(subscriber_decks__owner_id=user.id)
        # )

    def card_counts(self):
        '''
        Returns a dict mapping deck ID to card count for that deck.
        '''
        counts = (
            cards.Card.objects.available().filter(deck__in=self)
            .values('deck_id').annotate(card_count=Count('deck_id'))
        )
        per_deck_counts = {
            deck_id: 0 for deck_id in self.values_list('id', flat=True)
        }
        per_deck_counts.update({
            count['deck_id']: count['card_count'] for count in counts
        })
        return per_deck_counts

    def subscriber_counts(self):
        '''
        Returns a dict mapping deck ID to subscriber count for that deck.
        '''
        counts = self.model.objects.filter(synchronized_with__in=self).filter(
            active=True,
        ).values('synchronized_with_id').annotate(
            subscriber_count=Count('synchronized_with_id'),
        )
        subscriber_counts = {
            count['synchronized_with_id']: count['subscriber_count']
            for count in counts
        }
        subscriber_counts.update({
            deck_id: 0 for deck_id in self.values_list('id', flat=True)
            if deck_id not in subscriber_counts
        })
        return subscriber_counts


class Deck(models.Model):
    objects = DeckQuerySet.as_manager()

    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from='name', always_update=True, unique=False)
    image = models.ImageField(blank=True)
    description = models.TextField(max_length=2000, blank=True)
    owner = models.ForeignKey(User, db_index=True, editable=False)

    collection = models.ForeignKey('flashcards.DeckCollection',
        null=True, blank=True, related_name='decks')

    textbook_source = models.ForeignKey(Textbook, null=True, blank=True)

    randomize_card_order = models.BooleanField(default=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    # whether this is a publicly shared deck
    shared = models.BooleanField(default=False, blank=True)
    shared_at = models.DateTimeField(null=True, blank=True, editable=False)
    # or if not, whether it's synchronized with a shared deck
    synchronized_with = models.ForeignKey('self',
        null=True, blank=True, related_name='subscriber_decks')

    # "active" is just a soft deletion flag. "suspended" is temporarily
    # disabled.
    suspended = models.BooleanField(default=False, db_index=True)
    active = models.BooleanField(default=True, blank=True, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'flashcards'
        ordering = ('name',)
        #TODO-OLD unique_together = (('owner', 'name'), )

    @property
    def image_url(self):
        if self.image:
            url = self.image.url
        else:
            url = '/static/img/deck_icons/waves-{}.jpg'.format(
                (self.synchronized_with_id or self.id) % 8)
        return urljoin(settings.DEFAULT_URL_PREFIX, url)

    def original_author(self):
        # raise Exception("original author")
        if self.synchronized_with is not None:
            return self.synchronized_with.owner
        return self.owner

    def facts_with_cards_prefeteched(self):
        return self.facts.prefetch_related('card_set')

    @property
    def is_synchronized(self):
        return self.synchronized_with is not None

    def get_absolute_url(self):
        return reverse('deck_detail', kwargs={'deck_id': self.id})

    @property
    def share_url(self):
        if not self.shared:
            return
        return settings.DEFAULT_URL_PREFIX + reverse(
            'shared-deck-detail', kwargs={'pk': self.pk, 'slug': self.slug})

    def save(self, update_fields=None, *args, **kwargs):
        super(Deck, self).save(update_fields=update_fields, *args, **kwargs)

        update_kwargs = {}
        if update_fields is None or 'image' in update_fields:
            update_kwargs['image'] = self.image
        if update_fields is None or 'collection' in update_fields:
            update_kwargs['collection'] = self.collection
        if update_kwargs:
            self.subscriber_decks.update(**update_kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        '''
        Soft-deletes without propagating anything to subscribers.
        '''
        from manabi.apps.flashcards.models import Card

        self.active = False
        self.save(update_fields=['active'])

        self.facts.update(active=False)
        self.card_set.update(active=False)

        self.subscriber_decks.clear()

        for fact in self.facts.iterator():
            fact.subscriber_facts.clear()
        self.facts.update(active=False)

    @property
    def has_subscribers(self):
        '''
        Returns whether there are subscribers to this deck, because
        it is shared, or it had been shared before.
        '''
        return self.subscriber_decks.filter(active=True).exists()

    @transaction.atomic
    def share(self):
        '''
        Shares this deck publicly. Resynchronizes with any preexisting
        subscribers.
        '''
        if self.synchronized_with:
            raise TypeError(
                "Cannot share synchronized decks (decks which are already "
                "synchronized with shared decks).")

        self.shared = True
        self.shared_at = datetime.datetime.utcnow()
        self.save(update_fields=['shared', 'shared_at'])

        copy_facts_to_subscribers(self.facts.filter(active=True))

    @transaction.atomic
    def unshare(self):
        '''
        Unshares this deck.
        '''
        if not self.shared:
            raise TypeError("This is not a shared deck, so it cannot be unshared.")

        self.shared = False
        self.save(update_fields=['shared'])

    def get_subscriber_deck_for_user(self, user):
        '''
        Returns the subscriber deck for `user` of this deck.
        If it doesn't exist, returns None.
        If multiple exist, even though this shouldn't happen,
        we just return the first one.
        '''
        subscriber_decks = self.subscriber_decks.filter(owner=user, active=True)
        return subscriber_decks.first()

    #TODO implement subscribing with new stuff.
    @transaction.atomic
    def subscribe(self, user):
        '''
        Subscribes to this shared deck for the given user.
        They will study this deck as their own, but will
        still receive updates to content.

        Returns the newly created deck.

        If the user was already subscribed to this deck,
        returns the existing deck.
        '''
        from manabi.apps.flashcards.models import Card, Fact

        # Check if the user is already subscribed to this deck.
        subscriber_deck = self.get_subscriber_deck_for_user(user)
        if subscriber_deck:
            return subscriber_deck

        if not self.shared:
            raise TypeError('This is not a shared deck - cannot subscribe to it.')
        if self.synchronized_with:
            raise TypeError('Cannot share a deck that is already synchronized to a shared deck.')

        #TODO-OLD dont allow multiple subscriptions to same deck by same user

        deck = Deck.objects.create(
            synchronized_with=self,
            name=self.name,
            description=self.description,
            textbook_source=self.textbook_source,
            owner_id=user.id,
        )

        copy_facts_to_subscribers(self.facts.all(), subscribers=[user])

        return deck

    def card_count(self):
        return cards.Card.objects.of_deck(self).available().count()

    def subscriber_count(self):
        return self.subscriber_decks.count()

    def subscribers(self):
        return User.objects.filter(
            id__in=self.subscriber_decks.filter(active=True).values('owner_id')
        )

    #TODO-OLD kill - unused?
    #@property
    #def new_card_count(self):
    #    return Card.objects.approx_new_count(deck=self)
    #    #FIXME do for sync'd decks
    #    return cards.Card.objects.cards_new_count(
    #            self.owner, deck=self, active=True, suspended=False)

    #TODO-OLD kill - unused?
    #@property
    #def due_card_count(self):
    #    return cards.Card.objects.cards_due_count(
    #            self.owner, deck=self, active=True, suspended=False)

    @cached_function(namespace=deck_review_stats_namespace)
    def average_ease_factor(self):
        '''
        Includes suspended cards in the calcuation. Doesn't include inactive cards.
        '''
        average_ease_factor = self.card_set.filter(active=True).aggregate(
            Avg('ease_factor'))['ease_factor__avg']
        return average_ease_factor or DEFAULT_EASE_FACTOR
