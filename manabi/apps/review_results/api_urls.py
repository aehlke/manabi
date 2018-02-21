from django.conf.urls import *

from manabi.apps.review_results import api_views

urlpatterns = [
    url(r'^$', api_views.ReviewResultsView.as_view()),
]
