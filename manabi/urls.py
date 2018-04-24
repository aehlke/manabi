from django.conf import settings
from django.conf.urls import *
from django.contrib import admin
from django.views.generic.base import TemplateView
from rest_framework import routers
from rest_framework_social_oauth2.views import ConvertTokenView

import manabi.views
from manabi.apps.manabi_auth.api_views import UserCreateWithTokenView
from manabi.apps.flashcards.api_views import (
    DeckViewSet,
    SynchronizedDeckViewSet,
    SharedDeckViewSet,
    SuggestedSharedDecksViewSet,
    ManabiReaderFactViewSet,
    FactViewSet,
    ReviewAvailabilitiesViewSet,
    NextCardsForReviewViewSet,
    CardViewSet,
)
from manabi.apps.review_results.api_views import ReviewResultsView


api_router = routers.DefaultRouter()
api_router.register(r'flashcards/decks',
    DeckViewSet,
    base_name='deck')
api_router.register(r'flashcards/synchronized_decks',
    SynchronizedDeckViewSet,
    base_name='synchronized-deck')
api_router.register(r'flashcards/suggested_shared_decks',
    SuggestedSharedDecksViewSet,
    base_name='suggested-shared-deck')
api_router.register(r'flashcards/shared_decks',
    SharedDeckViewSet,
    base_name='shared-deck')
api_router.register(r'flashcards/facts',
    FactViewSet,
    base_name='fact')
api_router.register(r'flashcards/manabi_reader_facts',
    ManabiReaderFactViewSet,
    base_name='fact')
api_router.register(r'flashcards/cards',
    CardViewSet,
    base_name='card')
api_router.register(r'flashcards/review_availabilities',
    ReviewAvailabilitiesViewSet,
    base_name='card')
api_router.register(r'flashcards/next_cards_for_review',
    NextCardsForReviewViewSet,
    base_name='next-card-for-review')

urlpatterns = [
    url(r'^apple-app-site-association$', TemplateView.as_view(
        template_name='apple_app_site_association.json',
        content_type='application/json',
    )),

    url(r'^ios-required/', TemplateView.as_view(
        template_name='ios_required.html'), name='ios-required'),

    url(r'^accounts/', include('allauth.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^rq/', include('django_rq.urls')),

    url(r'^$', manabi.views.homepage, name='homepage'),
    url(r'^flashcards/', include('manabi.apps.flashcards.urls')),
    url(r'^reader_feeds/', include('manabi.apps.reader_feeds.urls')),
    url(r'^users/', include('manabi.apps.profiles.urls')),

    url(r'^terms-of-service/$', TemplateView.as_view(
        template_name='tos.html'), name='terms_of_service'),
    url(r'^privacy-policy/$', TemplateView.as_view(
        template_name='privacy.html'), name='privacy_policy'),
    url(r'^credits/$', TemplateView.as_view(
        template_name='credits.html'), name='credits'),

    # API URLs.
    url(r'^api/', include((api_router.urls, 'api'))),
    url(r'^api/auth/register/$', UserCreateWithTokenView.as_view(),
        name='register'),
    url(r'^api/auth/convert-token/$', ConvertTokenView.as_view()),
    url(r'^api/auth/', include('djoser.urls.authtoken')),
    url(r'^api/flashcards/', include('manabi.apps.flashcards.api_urls')),
    url(r'^api/flashcards/review_results/', include('manabi.apps.review_results.api_urls')),
    url(r'^api/subscriptions/', include('manabi.apps.subscriptions.api_urls')),
    url(r'^api/furigana/', include('manabi.apps.furigana.urls')),
    url(r'^api/twitter_usages/', include('manabi.apps.twitter_usages.urls')),
]

# if not settings.LIVE_HOST:
#    urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]
if 'silk' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]
