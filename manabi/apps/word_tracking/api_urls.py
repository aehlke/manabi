from rest_framework import routers

import .api_views

api_router = routers.DefaultRouter()

api_router.register(r'tracked_words', api_views.tracked_words)

urlpatterns = [
    url(r'^', include(api_router.urls, 'word_tracking_api')),
]
