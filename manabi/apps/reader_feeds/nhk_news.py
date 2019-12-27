# -*- encoding: utf-8 -*-
import asyncio
import re
from datetime import datetime
from time import mktime
from urllib.parse import urlparse, urlunparse, urljoin

import lxml.html
import feedparser
import pytz
from django.conf import settings
from feedgen.feed import FeedGenerator
from requests_html import AsyncHTMLSession


async def _get_image_url(article_url):
    session = AsyncHTMLSession()
    r = await session.get(article_url, timeout=20)
    doc = r.html.lxml
    return doc.cssselect('meta[property="og:image"]')[0].get('content')


async def _process_and_add_entry(post, fg):
    entry = fg.add_entry(order='append')

    title = post.title
    entry.title(title)

    published_struct = post['published_parsed']
    entry.published(
        datetime.fromtimestamp(mktime(published_struct))
        .replace(tzinfo=pytz.utc))

    article_url = post.link
    entry.id(article_url)
    entry.link({'href': article_url})

    image_url = await _get_image_url(article_url)
    if image_url:
        entry.link(href=image_url, rel='enclosure', type='image/jpeg')

    description = post.summary
    entry.description(description)

    return entry


async def generate_feed(
    entry_limit=None,
    return_content_only=False,
):
    fg = FeedGenerator()
    fg.id(f'http://www3.nhk.or.jp/news/')
    fg.title(f'NHKニュース')
    fg.language('ja')

    feed = feedparser.parse('https://www3.nhk.or.jp/rss/news/cat0.xml')

    entries = []
    for post in reversed(feed.entries):
        entry = await _process_and_add_entry(post, fg)

        if entry is not None:
            entries.append(entry)

        if entry is not None and entry_limit is not None:
            entry_limit -= 1

        if entry_limit <= 0:
            break

    if return_content_only:
        html = ''
        for entry in entries:
            title = entry.title()
            content = entry.content()['content']
            html += f'<h1>{title}</h1>{content}'
        return html

    if fg.entry() == 0:
        raise Exception("Generated zero feed entries.")

    return fg.atom_str(pretty=True, encoding='utf-8')
