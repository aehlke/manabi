from django.conf.urls import *

from manabi.apps.profiles import views

urlpatterns = [
    url(r'^(?P<username>\w+)/$', views.user_profile, name='user-profile'),
]
