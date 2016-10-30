from django.conf import settings
from django.conf.urls import *
from rest_framework import routers

from manabi.apps.flashcards import views
from manabi.apps.flashcards import api_views import

router = routers.SimpleRouter()
router.register(r'decks', api_views.DeckViewSet, base_name='deck')
router.register(r'facts', views.FactViewSet, base_name='fact')

urlpatterns = [
]

urlpatterns += router.urls
