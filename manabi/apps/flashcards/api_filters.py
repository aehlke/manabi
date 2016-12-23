from datetime import datetime

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from manabi.apps.flashcards.models import (
    Deck,
)


def _get_bool(request, field_name):
    value = request.query_params.get(field_name, 'false').lower()
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        raise ValidationError(
            "Invalid {} value.".format(field_name))

def _get_timestamp(request, field_name):
    value = request.query_params.get(field_name)
    if value is None:
        return
    try:
        datetime.fromtimestamp(float(value))
    except ValueError:
        raise ValidationError(
            "Invalid {} value.".format(field_name))


def review_availabilities_filters(request):
    deck = None
    deck_id = request.query_params.get('deck_id')
    if deck_id:
        deck = get_object_or_404(Deck, pk=deck_id)

    return {
        'deck': deck,
    }


def next_cards_to_review_filters(request):
    deck = None
    deck_id = request.query_params.get('deck_id')
    if deck_id:
        deck = get_object_or_404(Deck, pk=deck_id)

    early_review = _get_bool(request, 'early_review')
    early_review_began_at = _get_timestamp(request, 'early_review_began_at')

    include_new_buried_siblings = _get_bool(
        request, 'include_new_buried_siblings')

    new_cards_per_day_limit_override = (
       request.query_params.get('new_cards_per_day_limit_override'))
    if new_cards_per_day_limit_override is not None:
        new_cards_per_day_limit_override = int(
            new_cards_per_day_limit_override)

    return {
        'deck': deck,
        'early_review': early_review,
        'include_new_buried_siblings': include_new_buried_siblings,
        'new_cards_per_day_limit_override': new_cards_per_day_limit_override,
    }
