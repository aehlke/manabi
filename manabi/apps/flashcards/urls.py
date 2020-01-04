from django.conf import settings
from django.conf.urls import *
from rest_framework import routers

from manabi.apps.flashcards import views
from manabi.apps.flashcards import api_views

deck_detail = views.DeckViewSet.as_view({'get': 'retrieve'})
deck_facts = views.DeckViewSet.as_view({'get': 'facts'})
shared_deck_detail = views.SharedDeckViewSet.as_view({'get': 'retrieve'})
shared_deck_facts = views.SharedDeckViewSet.as_view({'get': 'facts'})

router = routers.SimpleRouter()
router.register(r'decks', views.DeckViewSet, basename='deck')
router.register(r'shared-decks', views.SharedDeckViewSet, basename='shared-deck')
router.register(r'facts', views.FactViewSet, basename='fact')

urlpatterns = [
    url(r'^decks/creator/', views.deck_creator, name='deck-creator'),
    url(r'^decks/(?P<pk>\d+)/(?P<slug>[\w-]+)/$', deck_detail, name='deck-detail'),
    url(r'^decks/(?P<pk>\d+)/(?P<slug>[\w-]+)/facts/$', deck_facts, name='deck-facts'),
    url(r'^shared-decks/(?P<pk>\d+)/(?P<slug>[\w-]+)/$', shared_deck_detail, name='shared-deck-detail'),
    url(r'^shared-decks/(?P<pk>\d+)/(?P<slug>[\w-]+)/facts/$', shared_deck_facts, name='shared-deck-facts'),
]

urlpatterns += router.urls
