from catnap.rest_resources import RestResource, RestModelResource
from django.urls import reverse

from manabi.apps.manabi_auth.rest_resources import UserResource


class DeckResource(RestModelResource):
    fields = [
        'id',
        'name',
        'description',
        'owner',
        'shared',
        'shared_at',
        'created_at',
        'modified_at',
        'suspended',
        'card_count',
    ]

    def get_url_path(self):
        return '' #TODO reverse('rest-deck', args=[self.obj.id])

    def get_data(self):
        data = super(DeckResource, self).get_data()
        data.update({
            'owner': UserResource(self.obj.owner).get_data(),
            'status_url': '', #TODO reverse('rest-deck_status', args=[self.obj.id]),
        })
        return data


class FactResource(RestModelResource):
    fields = [
        'id',
        'deck_id',

        'active',

        'expression',
        'reading',
        'meaning',

        'created_at',
        'modified_at',
    ]

    def get_url_path(self):
        return ''  # TODO return reverse('api_fact', args=[self.obj.id])

    def get_data(self):
        data = super(FactResource, self).get_data()

        data.update({
            'card_count': self.obj.card_set.filter(active=True).count(),
        })

        return data


class CardReviewsResource(RestResource):
    def __init__(self, card):
        self.card = card

    def get_url_path(self):
        return reverse('api_card_review', args=[self.card.obj.id])


class CardResource(RestModelResource):
    fields = [
        'id',
        'deck_id',
        'fact_id',
        'ease_factor',
        'interval',
        'due_at',
        'last_ease_factor',
        'last_interval',
        'last_due_at',
        'review_count',
        'template',
    ]

    def get_url_path(self):
        return reverse('api_card', args=[self.obj.id])

    def get_data(self):
        data = super(CardResource, self).get_data()

        fact = self.obj.fact

        data.update({
            'expression': fact.expression,
            'reading': fact.reading,
            'meaning': fact.meaning,
        })

        return data
