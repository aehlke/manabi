from django.http import HttpResponse
from django.views.decorators.cache import cache_page, cache_control

from manabi.apps.reader_feeds.nhk_easy_news import (
    generate_nhk_easy_news_feed,
)


FEED_MAX_AGE = 60 * 60 * 4


@cache_page(60 * 60)
@cache_control(max_age=FEED_MAX_AGE)
def nhk_easy_news(request):
    feed_content = generate_nhk_easy_news_feed()
    return HttpResponse(
        feed_content,
        content_type='application/rss+xml; charset=utf-8',
    )
