from django.urls import path, include
from rest_framework import routers

from . import api_views

api_router = routers.DefaultRouter()

api_router.register(
    r'tracked_words',
    api_views.TrackedWordsViewSet,
    basename='tracked-words')

urlpatterns = [
    path(r'', include(api_router.urls)),
]
