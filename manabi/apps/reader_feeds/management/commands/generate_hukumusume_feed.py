# -*- encoding: utf-8 -*-
import re
from urlparse import urljoin

import requests
from django.core.management.base import BaseCommand, CommandError
from feedgen.feed import FeedGenerator
from lxml import html


def _month_urls(section):
    for month in range(1, 13):
        yield (section, month, 'http://hukumusume.com/douwa/pc/{}/itiran/{:02}gatu.htm'.format(section, month))


def _fetch_root(url):
        resp = requests.get(url)
        resp.raise_for_status()
        return html.fromstring(resp.content, base_url=url)


def execute():
    feed_items = {}
    added_entry_urls = set()
    sections = {
        'jap': u"日本の昔話 (Japanese Legends)",
        'minwa': u"日本の民話 (Japanese Folktales)",
        'world': u"世界の昔話 (World Folktales)",
        'aesop': u"イソップ童話 (Aesop's Fables)",
        'kobanashi': u"江戸小話 (Edo Short Stories)",
        'kaidan': u"百物語 (Japanese Ghost Stories)",
    }
    for section in sections:
        feed_items[section] = []
    for batch in [_month_urls(section) for section in sections]:
        for section, month, month_url in batch:
            root = _fetch_root(month_url)

            for link in root.cssselect('a'):
                url = urljoin(month_url, link.get('href'))
                if url in added_entry_urls:
                    continue
                if re.match(
                    r'^http://hukumusume.com/douwa/pc/(jap|minwa|world|aesop|kobanashi|kaidan)/{:02}/\w+\.html?$'.format(month),
                    url,
                ):
                    title = link.text
                    if not title:
                        continue

                    table = link.xpath('./ancestor::table[1]')[0]
                    texts = table.itertext()
                    description = ''
                    for text1, text2 in zip(texts, list(texts)[1:]):
                        if u'内容 :' in text1:
                            description = (text1 + text2)[len(u'内容 :'):]

                    try:
                        image_relative_url = table.cssselect('img')[0].get('src')
                        # Avoid weird case with "001", "002" links in Aesop feed (and maybe elsewhere).
                        if 'corner' in image_relative_url:
                            continue
                        image_url = urljoin(month_url, image_relative_url)
                    except IndexError:
                        # Every one has an image.
                        continue

                    feed_items[section].append({
                        'url': url,
                        'title': link.text,
                        'description': description,
                        'image_url': image_url,
                    })
                    added_entry_urls.add(url)

    for section, title in sections.items():
        fg = FeedGenerator()
        fg.id('http://hukumusume.com/douwa/pc/{}/index.html'.format(section))
        fg.title(title)
        fg.language('ja')

        for item in feed_items[section]:
            entry = fg.add_entry()
            entry.id(item['url'])
            entry.title(item['title'])
            entry.link(href=item['url'], rel='alternate')
            entry.summary(item['description'])
            entry.content('<img src="{}" />'.format(item['image_url']), type='CDATA')

        fg.atom_file('manabi/static/reader/feeds/hukumusume-{}.rss'.format(section))


class Command(BaseCommand):
    def handle(self, *args, **options):
        execute()
