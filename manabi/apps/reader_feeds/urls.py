from django.conf.urls import url

from manabi.apps.reader_feeds import views

urlpatterns = [
    url(r'nhk_easy_news.rss$', views.nhk_easy_news),
]
