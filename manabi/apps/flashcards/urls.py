from django.conf import settings
from django.conf.urls import *
from rest_framework import routers

from manabi.apps.flashcards import views
from manabi.apps.flashcards import api_views

deck_detail = views.DeckViewSet.as_view({'get': 'retrieve'})

router = routers.SimpleRouter()
router.register(r'decks', views.DeckViewSet, base_name='deck')
router.register(r'facts', views.FactViewSet, base_name='fact')

urlpatterns = [
    url(r'^decks/(?P<pk>\d+)/(?P<deck_slug>[\w-]+)/$', deck_detail, name='deck-detail'),
]

urlpatterns += router.urls
