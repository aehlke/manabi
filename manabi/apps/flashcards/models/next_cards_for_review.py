import pytz
from datetime import datetime

from manabi.apps.flashcards.models import (
    Card,
)
from manabi.apps.flashcards.models.new_cards_limit import (
    NewCardsLimit,
)


class ReviewInterstitial(object):
    def __init__(
        self,
        user,
        deck=None,
        new_cards_per_day_limit_override=None,
        excluded_card_ids=set(),
        time_zone=None,
        new_cards_limit=None,
        buffered_cards_count=None,
        buffered_new_cards_count=None,
    ):
        '''
        `new_cards_limit` is an instance of `NewCardsLimit.`
        '''
        from manabi.apps.flashcards.models.review_availabilities import (
            ReviewAvailabilities,
        )

        self.review_availabilities = ReviewAvailabilities(
            user,
            deck=deck,
            excluded_card_ids=excluded_card_ids,
            new_cards_per_day_limit_override=new_cards_per_day_limit_override,
            time_zone=time_zone,
            new_cards_limit=new_cards_limit,
            buffered_cards_count=buffered_cards_count,
            buffered_new_cards_count=buffered_new_cards_count,
        )


class NextCardsForReview(object):
    def __init__(
        self,
        user,
        count,
        deck=None,
        early_review=False,
        early_review_began_at=None,
        include_new_buried_siblings=False,
        new_cards_per_day_limit_override=None,
        excluded_card_ids=set(),
        time_zone=None,
    ):
        new_cards_limit = NewCardsLimit(
            user,
            new_cards_per_day_limit_override=new_cards_per_day_limit_override,
        )

        next_cards = Card.objects.next_cards(
            user,
            count,
            excluded_ids=excluded_card_ids,
            deck=deck,
            early_review=early_review,
            early_review_began_at=early_review_began_at,
            include_new_buried_siblings=include_new_buried_siblings,
            new_cards_limit=new_cards_limit.next_new_cards_limit,
        )

        card_ids = [card.id for card in next_cards]

        # FIXME don't need 2 queries here...
        self.cards = (
            Card.objects
            .filter(pk__in=card_ids)
            .select_related('fact')
        )

        excluded_card_ids.update(card_ids)
        buffered_new_cards_count = len([
            card for card in self.cards if card.is_new
        ])

        self.interstitial = ReviewInterstitial(
            user,
            deck=deck,
            time_zone=time_zone,
            excluded_card_ids=excluded_card_ids,
            buffered_cards_count=len(self.cards),
            buffered_new_cards_count=buffered_new_cards_count,
            new_cards_per_day_limit_override=new_cards_per_day_limit_override,
            new_cards_limit=new_cards_limit,
        )

        self.server_datetime = datetime.now(pytz.utc)
