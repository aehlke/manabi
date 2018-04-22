from manabi.apps.utils import query_cleaner
from manabi.apps.utils.query_cleaner import clean_query
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.humanize.templatetags.humanize import naturalday
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, loader
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from dojango.decorators import json_response
from dojango.util import to_dojo_data, json_decode, json_encode
from manabi.apps.flashcards.models import CardHistory, Card
from manabi.apps.flashcards.models.constants import GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY
from manabi.apps.flashcards.views.decorators import flashcard_api as api
from manabi.apps.flashcards.views.decorators import has_card_query_filters


@login_required
def index(request):
    context = {
    }
    return render_to_response('stats/index.html', context,
        context_instance=RequestContext(request))





# Views for graphs


MATURITY_COLORS = {
    'new':      '#62C691',
    'young':    '#7074C5',#'#49388a',
    'mature':   '#E4C670',
}

MATURITY_NAMES = {
    'new': 'New',
    'young': 'Started',
    'mature': 'Proficient',
}


@api
@require_GET
def repetitions(request):
    '''
    Graph data for repetitions per day.
    '''
    series = []
    user = request.user
    user_items = CardHistory.objects.of_user(user)

    for maturity in ['new', 'young', 'mature']:
        data = getattr(user_items, maturity)().repetitions()

        # Convert the values into pairs (from hashes)
        data = list((value['reviewed_on'], value['repetitions'])
                      for value in data)

        series.append({
            'name': MATURITY_NAMES.get(maturity, maturity),
            'data': data,
            'color': MATURITY_COLORS[maturity],
        })

    return {'series': series}

@api
@require_GET
def due_counts(request):
    '''Due per day in future.'''
    series = []
    user = request.user
    user_items = Card.objects.common_filters(user)

    for maturity in ['young', 'mature']:
        items = getattr(user_items, maturity)(user)

        today_count = items.due_today_count()

        data = [(datetime.today(), today_count,)]

        future_counts = getattr(user_items, maturity)(user).future_due_counts()

        # Convert the values into pairs (from hashes)
        data.extend(list((value['due_on'], value['due_count'])
                      for value in future_counts))

        series.append({
            'name': MATURITY_NAMES.get(maturity, maturity),
            'data': data,
            'color': MATURITY_COLORS[maturity],
        })

    return {'series': series}



@api
@require_GET
@has_card_query_filters
def daily_repetition_history(request, deck=None, tags=None):
    '''
    For now, just gives review counts per day. Doesn't split into correct/incorrect.
    The last element is today. Each element before that is one day earlier.
    '''
    # How many days of history?
    days = int(request.GET.get('days', 60))
    from_ = datetime.utcnow() - timedelta(days=days)

    user_items = CardHistory.objects.of_user(request.user).filter(
        reviewed_at__gte=from_)

    if deck:
        user_items = user_items.of_deck(deck)

    data = [val['repetitions'] for val in user_items.repetitions()]
    return data

    #return [199, 115, 64, 92, 40, 60, 56, 85, 2, 4, 8, 64, 41, 1, 44, 19, 115, 64, 82, 40, 60, 56, 5, 288, 4, 8, 64, 41, 1, 44]
    #return {
    #    'series': [
    #        {
    #            'color': 'green',
    #            'data': [29.9, 71.5, 106.4, 129.2, 144.0, 176.0, 135.6, 148.5, 216.4, 194.1, 95.6, 54.4]
    #        },
    #        {
    #            'color': 'red',
    #            'data': [19.9, 11.5, 6.4, 9.2, 4.0, 6.0, 5.6, 8.5, 6.4, 4.1, 1, 4.4]
    #        }
    #    ]
     #}







########################################
#
# Used for end of review session stats
#
########################################

#TODO-OLD needed? so far, unused.
#@api
#@require_GET
#@has_card_query_filters
#def scheduling_summary(request, deck=None, tags=None):
#    '''
#    Provides the following data:
#        # due now
#        # due tomorrow
#        # new cards
#        next card's due date (datetime)
#    '''
#    cards = Card.objects.common_filters(
#        request.user, deck=deck, tags=tags)

#    data = {
#        'due_now': cards.due(request.user).count(),
#        'due_tomorrow': Card.objects.count_of_cards_due_tomorrow(
#                request.user, deck=deck, tags=tags),
#        'new': cards.new().count(),
#        'next_card_due_at': cards.next_card_due_at(),
#    }
#    return data



########################################
#
# Individual card and deck stats
#
########################################


#@api
#@require_GET
#def card_stats_json(request, card_id):
#    '''
#    '''
#    card = get_object_or_404(Card, pk=card_id)

#    if card.owner != request.user:
#        raise PermissionDenied('You do not own this flashcard.')

#    #first_reviewed_at = card.cardhistory_set.

#    stats = {
#        'createdAt':        card.fact.created_at,
#        'modifiedAt':       card.fact.modified_at,
#        'firstReviewedAt':  card.first_reviewed_at,
#        'dueAt':            card.due_at,
#        'interval':         card.interval,
#        'easeFactor':       card.ease_factor,
#        'lastDueAt':        card.last_due_at,
#        'lastInterval':     card.last_interval,
#        'lastEaseFactor':   card.last_ease_factor,
#        'lastFailedAt':     card.last_failed_at,
#        'lastReviewGrade':  card.last_review_grade,
#        'reviewCount':      card.review_count,

#        'averageDuration':         card.average_duration(),
#        'averageQuestionDuration': card.average_question_duration(),
#        'totalDuration':           card.total_duration(),
#        'totalQuestionDuration':   card.total_question_duration(),

#        'template':         card.template,
#    }

#    return stats


@login_required
def card_stats(request, card_id):
    '''
    Similar to `card_stats_json` but actually renders it in HTML.
    '''
    card = get_object_or_404(Card, pk=card_id)

    if not card.deck.shared and card.owner != request.user:
        raise PermissionDenied('You do not own this flashcard.')

    context = {
        'card': card,
        'early_review': card.due_at and card.due_at > datetime.utcnow(),
    }

    return render_to_response('stats/card_stats.html', context,
        context_instance=RequestContext(request))
    


