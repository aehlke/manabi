from django.conf.urls import *

from manabi.apps.subscriptions import api_views


urlpatterns = [
    url(r'^purchasing_options/$', api_views.purchasing_options),
    url(r'^manabi_reader_purchasing_options/$',
        api_views.manabi_reader_purchasing_options),
    url(r'^subscription_status/$', api_views.subscription_status),
    url(r'^subscriptions/$', api_views.SubscriptionViewSet.as_view(
        {'post': 'create'})),
    url(r'^subscription_update_notification/$',
        api_views.subscription_update_notification),
]
