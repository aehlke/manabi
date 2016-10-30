from django.conf.urls import *

from manabi.apps.furigana import api_views

urlpatterns = [
    url(r'^inject/$', api_views.inject_furigana),
]
