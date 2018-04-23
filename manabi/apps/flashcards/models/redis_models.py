from manabi.apps.utils.utils import unix_time
from manabi.apps.manabi_redis.models import redis


class RedisCard:
    def __init__(self, card):
        self.card = card

    #def update_due_at(self):
    #    ''' Records the earliest due card per fact. '''
    #    key = 'next_due_at:fact:{0}'.format(self.card.fact_id)
    #    score = unix_time(self.card.due_at)
    #    existing = redis.get(key)
    #    if existing is None or int(existing) > score:
    #        redis.zadd(key, score, self.card.id)

    #def _update_review_date(self):
    #    ''' Records the most recently reviewed card per card. '''
    #    key = 'last_reviewed_at:fact:{0}'.format(self.card.fact_id)
    #    score = unix_time(card.last_reviewed_at)
    #    existing = redis.get(key)
    #    if existing is None or int(existing) < score:
    #        redis.zadd(key, score, card.id)

    #def _add_failed_review(self):
    #    ''' Which cards were failed in their last review, per user. '''
    #    if self.card.last_review_grade != GRADE_NONE:
    #        return
    #    key = 'failed_cards:user:{0}'.format(self.card.owner)
    #    redis.sadd(key, self.card.id)

    def update_deck(self):
        key = 'cards:deck:{0}'.format(self.card.fact.deck_id)
        redis.sadd(key, self.card.id)

    def update_ease_factor(self):
        key = 'ease_factor:deck:{0}'.format(self.card.fact.deck_id)
        if self.card.active and self.card.ease_factor:
            score = self.card.ease_factor
            redis.zadd(key, score, self.card.id)
        else:
            redis.zrem(key, self.card.id)

    def update_card_owner(self):
        key = 'cards:owner:%s' % self.card.fact.deck.owner_id
        redis.sadd(key, self.card.id)

    def after_review(self):
        ''' Call after a card is reviewed. '''
        #self._update_review_date()
        #self._add_failed_review()
        #self.update_due_at()
        self.update_ease_factor()

    def update_all(self):
        self.update_deck()
        self.update_ease_factor()
        self.update_card_owner()

    def delete(self):
        deck_id = card.fact.deck_id
        redis.srem('cards:deck:%s' % deck_id, card.id)
        redis.zrem('ease_factor:deck:%s' % deck_id, card.id)
        redis.srem('cards:owner:%s' % card.fact.deck.owner_id, card.id)
