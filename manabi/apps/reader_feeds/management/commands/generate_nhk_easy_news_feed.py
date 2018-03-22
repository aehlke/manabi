# -*- encoding: utf-8 -*-
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from manabi.apps.reader_feeds.feed_storage import save_feed
from manabi.apps.reader_feeds.nhk_easy_news import generate_nhk_easy_news_feed


class Command(BaseCommand):
    def handle(self, *args, **options):
        xml = generate_nhk_easy_news_feed()
        save_feed('nhk_easy_news.rss', xml)
