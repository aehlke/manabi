from django.conf import settings
from django.conf.urls import *
from rest_framework import routers

from manabi.apps.flashcards import views
from manabi.apps.flashcards.api_views import (
    DeckViewSet,
)

router = routers.SimpleRouter()
router.register(r'decks', DeckViewSet, base_name='deck')

urlpatterns = [
]

urlpatterns += router.urls
