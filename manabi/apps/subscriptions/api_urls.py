from django.conf.urls import *

from manabi.apps.subscriptions import api_views


urlpatterns = [
    url(r'^purchasing_options/$', api_views.purchasing_options),
    url(r'^subscriptions/$', api_views.SubscriptionViewSet.as_view()),
]
