import datetime
from datetime import timedelta
from itertools import chain

from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Q, F, Avg, Max, Min, Count

from manabi.apps.manabi_redis.models import redis
from manabi.apps.flashcards.models.constants import GRADE_NONE, MATURE_INTERVAL_MIN
from manabi.apps.flashcards.models.burying import with_siblings_buried


class SchedulerMixin(object):
    '''
    Methods for retrieving the next cards that are ready to be reviewed.
    '''

    def _next_failed_due_cards(
        self, user, initial_query, count, review_time, buried_facts,
        **kwargs
    ):
        if not count:
            return []

        # Don't space/bury these based on FactQuerySet.buried (Or should we?)
        cards = initial_query.filter(
            last_review_grade=GRADE_NONE,
            due_at__isnull=False,
            due_at__lte=review_time)
        cards = with_siblings_buried(cards, 'due_at')

        return cards[:count]

    def _next_not_failed_due_cards(
        self,
        user,
        initial_query,
        count,
        review_time,
        buried_facts,
        **kwargs
    ):
        '''
        Returns the first [count] cards from initial_query which are due,
        weren't failed the last review, and  taking spacing of cards from
        the same fact into account.

        review_time should be datetime.datetime.utcnow()
        '''
        if not count:
            return []

        cards = initial_query.exclude(
            last_review_grade=GRADE_NONE).filter(
            due_at__isnull=False,
            due_at__lte=review_time)
        cards = cards.exclude(fact__in=buried_facts)
        cards = with_siblings_buried(cards, '-interval')

        #TODO-OLD Also get cards that aren't quite due yet, but will be soon,
        # and depending on their maturity
        # (i.e. only mature cards due soon).
        # Figure out some kind of way to prioritize these too.

        return cards[:count]

    def _next_failed_not_due_cards(
        self, user, initial_query, count, review_time, buried_facts,
        **kwargs
    ):
        if not count:
            return []

        #TODO-OLD prioritize certain failed cards, not just by due date
        # We'll show failed cards even if they've been reviewed recently.
        # This is because failed cards are set to be shown 'soon' and not
        # just in 10 minutes. Special rules.
        #TODO-OLD we shouldn't show mature failed cards so soon though!
        #TODO-OLD randomize the order (once we fix the Undo)

        # Don't space/bury these (Or should we?)
        cards = initial_query.filter(
            last_review_grade=GRADE_NONE, due_at__gt=review_time)
        cards = cards.exclude(fact__in=buried_facts)
        cards = with_siblings_buried(cards, 'due_at')

        return cards[:count]

    def _next_new_cards(
        self,
        user,
        initial_query,
        count,
        review_time,
        buried_facts,
        include_new_buried_siblings=False,
        learn_more=False,  # DEPRECATED?
        new_cards_limit=None,
        **kwargs
    ):
        from manabi.apps.flashcards.models.cards import CARD_TEMPLATE_CHOICES
        from manabi.apps.flashcards.models.facts import Fact

        count = min(count, new_cards_limit)

        if not count:
            return []

        cards = initial_query.filter(due_at__isnull=True)
        cards = cards.exclude(fact__in=buried_facts)
        cards = with_siblings_buried(cards, 'new_card_ordinal')
        cards = list(cards[:count])

        # Add spaced cards if in early review/learn more mode and we haven't
        # supplied enough.
        if (include_new_buried_siblings or learn_more) and len(cards) < count:
            buried_cards = initial_query.filter(due_at__isnull=True)
            buried_cards = buried_cards.exclude(pk__in=cards)
            buried_cards = buried_cards.order_by('new_card_ordinal')
            cards.extend(list(buried_cards[:count - len(cards)]))

        return cards

    def _next_due_soon_cards(
        self,
        user,
        initial_query,
        count,
        review_time,
        buried_facts,
        **kwargs
    ):
        '''
        Used for early review. Ordered by due date.
        '''
        if not count:
            return []

        cards = initial_query.exclude(last_review_grade=GRADE_NONE)
        cards = cards.filter(due_at__gt=review_time)

        priority_cutoff = review_time - datetime.timedelta(minutes=60)
        staler_cards = cards.filter(last_reviewed_at__gt=priority_cutoff)
        staler_cards = staler_cards.exclude(fact__in=buried_facts)
        staler_cards = staler_cards.order_by('due_at')

        return staler_cards[:count]

    def _next_due_soon_cards2(
        self,
        user,
        initial_query,
        count,
        review_time,
        buried_facts,
        **kwargs
    ):
        if not count:
            return []

        cards = initial_query.exclude(last_review_grade=GRADE_NONE)
        cards = cards.filter(due_at__gt=review_time)

        priority_cutoff = review_time - datetime.timedelta(minutes=60)
        fresher_cards = cards.filter(
            last_reviewed_at__isnull=False,
            last_reviewed_at__lte=priority_cutoff)
        fresher_cards = fresher_cards.exclude(fact__in=buried_facts)
        fresher_cards = fresher_cards.order_by('due_at')

        return fresher_cards[:count]

    def _next_card_funcs(
            self,
            early_review=False,
            learn_more=False,
    ):
        if early_review and learn_more:
            raise ValueError("Cannot set both early_review and learn_more together.")

        card_funcs = [
            self._next_failed_due_cards,        # due, failed
            self._next_not_failed_due_cards,    # due, not failed
            self._next_failed_not_due_cards,    # failed, not due
        ]

        if early_review:
            card_funcs.extend([
                self._next_due_soon_cards,
                self._next_due_soon_cards2, # Due soon, not yet, but next in the future.
            ])
        elif learn_more:
            # TODO: Only new cards, and ignore spacing.
            # Unless we don't need learn_more anymore...
            card_funcs = [self._next_new_cards]
        else:
            card_funcs.extend([self._next_new_cards]) # New cards at end.

        return card_funcs

    def next_cards(
        self,
        user,
        count,
        deck=None,
        new_cards_limit=None,
        excluded_ids=[],
        early_review=False,
        include_new_buried_siblings=False,
        learn_more=False,
    ):
        '''
        Returns `count` cards to be reviewed, in order.
        count should not be any more than a short session of cards
        set `early_review` to True for reviewing cards early
        (following any due cards)

        `include_new_buried_siblings` is used to allow learning
        cards whose siblings have already been learned recently.

        DEPRECATED:
        If learn_more is True, only new cards will be chosen,
        even if they were spaced due to sibling reviews.

        "Due soon" cards won't be chosen in this case,
        contrary to early_review's normal behavior.
        (#TODO-OLD consider changing this to have a separate option)

        `new_cards_limit` is an integer.
        '''
        from manabi.apps.flashcards.models.facts import Fact

        #TODO-OLD somehow spread some new cards into the early review
        # cards if early_review==True
        #TODO-OLD use args instead, like *kwargs etc for these funcs
        now = datetime.datetime.utcnow()

        card_funcs = self._next_card_funcs(
            early_review=early_review,
            learn_more=learn_more,
        )

        user_cards = self.common_filters(
            user, deck=deck, excluded_ids=excluded_ids)

        facts = Fact.objects.deck_facts(deck)
        buried_facts = facts.buried(
            user, review_time=now, excluded_card_ids=excluded_ids)

        cards_left = count
        card_queries = []

        for card_func in card_funcs:
            if not cards_left:
                break

            cards = card_func(
                user,
                user_cards,
                cards_left,
                now,
                early_review=early_review,
                include_new_buried_siblings=include_new_buried_siblings,
                learn_more=learn_more,
                buried_facts=buried_facts,
                new_cards_limit=new_cards_limit,
            )

            cards_left -= len(cards)

            if len(cards):
                card_queries.append(cards)

        #FIXME add new cards into the mix when there's a defined
        # new card per day limit
        #for now, we'll add new ones to the end
        return chain(*card_queries)


class CommonFiltersMixin(object):
    '''
    Provides filters for decks, maturity level, etc.

    This is particularly useful with view URLs which take query params for
    these things.
    '''
    def available(self):
        ''' Cards which are active and unsuspended. '''
        return self.filter(active=True, suspended=False)

    def of_deck(self, deck):
        return self.filter(deck=deck)

    def of_user(self, user):
        if not user.is_authenticated():
            return self.none()
        return self.filter(deck__owner=user)

    def excluding_ids(self, excluded_ids):
        return self.exclude(id__in=excluded_ids)

    def unsuspended(self):
        return self.filter(suspended=False)

    def common_filters(self, user, deck=None, excluded_ids=None):
        cards = self.of_user(user).unsuspended().filter(active=True)

        if deck:
            cards = cards.of_deck(deck)
        else:
            cards = cards.filter(deck__owner=user).exclude(deck__suspended=True)

        if excluded_ids:
            cards = cards.excluding_ids(excluded_ids)

        return cards

    def new(self, user):
        user_cards = self.available().of_user(user)
        return user_cards.filter(last_reviewed_at__isnull=True)

    def new_count(self, user, including_buried=True):
        '''
        Use this rather than `new(user).count()` for future-proofing.
        '''
        new_cards = self.new(user)
        if not including_buried:
            new_cards = with_siblings_buried(new_cards)
        return new_cards.count()

    def approx_new_count(self, user=None, deck=None):
        '''
        Approximates how many new cards are actually available to review.
        Will be between what new_count and unspaced_new_count return,
        but much faster than the latter.
        '''
        cards = self.available()
        if deck:
            cards = cards.of_deck(deck)
        return cards.new(user).values_list('fact_id').distinct().count()

    # def unspaced_new_count(self, user):
    #     '''
    #     Same as `new_count`, except it subtracts new cards that
    #     will be delayed due to sibling spacing (cards which haven't
    #     been spaced.)
    #     '''
    #     local_query = self.new(user).available()
    #     desired_count = 999999 #TODO-OLD use more elegant solution.
    #     now = datetime.datetime.utcnow()

    #     new_cards = self.new(user)

    #     return self._next_new_cards(user, local_query, desired_count, now).count()

    def young(self, user):
        return self.filter(
            last_reviewed_at__isnull=False,
            interval__isnull=False,
            interval__lt=MATURE_INTERVAL_MIN
        )

    def mature(self, user):
        return self.filter(
            interval__gte=MATURE_INTERVAL_MIN
        )

    def due(self, user, _space_cards=False):
        '''
        TODO: `_space_cards` is whether to space out due cards before returning
        them (which can result in fewer being returned).
        '''
        #TODO: Make _space_cards True by default.
        now = datetime.datetime.utcnow()
        due_cards = self.of_user(user).available().filter(
            due_at__isnull=False,
            due_at__lte=now,
        )

        if _space_cards:
            self._space_cards(due_cards, due_cards.count(), now)

            # Re-get them since some may have been spaced
            due_cards = due_cards.filter(
                due_at__lte=now)

        return due_cards.order_by('-interval')

    def count_of_cards_due_tomorrow(self, user):
        '''
        Returns the number of cards due by tomorrow at the same time
        as now. Doesn't take future spacing into account though, so it's
        a somewhat rough estimate.

        No longer includes new cards in its count.
        '''
        #from manabi.apps.flashcards.models.facts import Fact
        #cards = self.of_user(user)
        #if deck:
        #    cards = cards.filter(fact__deck=deck)
        #if tags:
        #    facts = usertagging.models.UserTaggedItem.objects.get_by_model(
        #            Fact, tags)
        #    cards = cards.filter(fact__in=facts)

        this_time_tomorrow = (datetime.datetime.utcnow()
                              + datetime.timedelta(days=1))
        cards = self.filter(
            due_at__isnull=False,
            due_at__lt=this_time_tomorrow,
        )
        due_count = cards.count()

        #new_count = self.new().count()
        #new_count = self.common_filters(
                #user, deck=deck, tags=tags).new().count()
        #new_count = min(
            #NEW_CARDS_PER_DAY,
            #self.new_cards_count(user, [], deck=deck, tags=tags))
        #return due_count + new_count
        return due_count

    def next_card_due_at(self):
        '''
        Returns the due date of the next due card.
        If one is already due, this will be in the past.
        '''
        return self.aggregate(Min('due_at'))['due_at__min']

    #def spaced_cards_new_count(self, user, deck=None):
        #threshold_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
        #recently_reviewed = self.filter(fact__deck__owner=user, fact__deck=deck, last_reviewed_at__lte=threshold_at)
        #facts = Fact.objects.filter(id__in=recently_reviewed.values_list('fact', flat=True))
        #new_cards_count = self.new_cards(user, deck).exclude(fact__in=facts).count()
        #return new_cards_count


class CardStatsMixin(object):
    '''Stats data methods, primarily used for graphs and things.'''

    def with_due_dates(self):
        '''
        Adds a `due_on` DateField-like value. Same as `due_at` minus its
        time information -- so just the day.
        '''
        return self.extra(select={'due_on': 'date(due_at)'})

    def due_counts(self):
        '''Number of cards due per day in the future.'''
        return self.with_due_dates().values('due_on').annotate(
            due_count=Count('id'))

    def due_today_count(self):
        '''The # of cards already due right now or later today.'''
        return self.filter(
            due_at__isnull=False,
            due_at__lte=datetime.datetime.today()).count()

    def future_due_counts(self):
        '''Same as `due_counts` but only for future, after today.'''
        return self.filter(
            due_at__gt=datetime.datetime.today()).with_due_dates().values(
            'due_on').annotate(due_count=Count('id'))


class CardQuerySet(CommonFiltersMixin, SchedulerMixin, CardStatsMixin, QuerySet):
    pass
