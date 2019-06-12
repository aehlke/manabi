from django.conf.urls import *

from manabi.apps.flashcards import api_views


urlpatterns = [
    # url(r'^next_cards_for_review/$', api.NextCardsForReview.as_view()),
    url(r'^undo_card_review/$', api_views.UndoCardReviewView.as_view()),
    url(r'^suspend_facts/$', api_views.SuspendFactsView.as_view()),
    # url(r'^cards/(?P<card>\w+)/$', api.Card.as_view(), name='api_card'),
    # url(r'^cards/(?P<card>\w+)/review/$', api.CardReview.as_view(), name='api_card_review'),

    # url(r'^decks/$', api.Decks.as_view(), name='api_decks'),
    # url(r'^decks/(?P<deck>\w+)/facts/$', api.DeckFacts.as_view(), name='api_deck_facts'),
    # url(r'^decks/(?P<deck>\w+)/cards/$', api.DeckCards.as_view(), name='api_deck_cards'),

    # url(r'^shared_decks/$', api.SharedDecks.as_view(), name='api_shared_decks'),
]
