# -*- encoding: utf-8 -*-
import asyncio
import subprocess
import tempfile

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from manabi.apps.reader_feeds.feed_storage import save_feed
from manabi.apps.reader_feeds.slow_communication import generate_feed


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--dev', action='store_true')
        parser.add_argument('--entry-limit', type=int, default=None)

    async def run(self, *args, **options):
        feed_kwargs = {}
        if options['entry_limit'] is not None:
            feed_kwargs['entry_limit'] = options['entry_limit']
        if options['dev']:
            feed_kwargs['return_content_only'] = True

        xml = await generate_feed(**feed_kwargs)

        if options['dev']:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix='.html',
            ) as tf:
                tf.write(f'<html><body>{xml}</body></html>'.encode('utf-8'))
            subprocess.call(['open', tf.name])
        else:
            save_feed(f'slow-communication.rss', xml)

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run(*args, **options))
        loop.close()
