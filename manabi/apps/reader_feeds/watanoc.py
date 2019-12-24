# -*- encoding: utf-8 -*-
import asyncio
import re
from datetime import datetime
from urllib.parse import urlparse, urlunparse, urljoin

import lxml.html
import feedparser
import praw
import pytz
import requests
from django.conf import settings
from feedgen.feed import FeedGenerator
from lxml.cssselect import CSSSelector
from lxml import etree
from requests_html import AsyncHTMLSession

ATTEMPTS_PER_ENTRY = 5


async def _get_audio_url(article_url):
    session = AsyncHTMLSession()
    r = await session.get(article_url, timeout=20)
    audio_source = r.html.find('audio source[type="audio/mpeg"]', first=True)
    try:
        return audio_source.attrs.get('src')
    except AttributeError:
        return None


async def _add_entries_from_page(page_url, response, fg, jlpt_level):
    entries = []

    for article in response.html.find(
        '#content section.loop-section article.loop-article',
    ):
        title = article.find('.entry-title a', first=True).text.replace(
            f'...({jlpt_level})', ' ')
        if 'quiz' in title.lower():
            continue

        entry = fg.add_entry()

        article_url = article.find('.entry-title a', first=True).attrs['href']
        entry.id(article_url)
        entry.link({'href': article_url})

        image_url = article.find('img.wp-post-image', first=True).attrs['src']
        entry.link(href=image_url, rel='enclosure', type='image/jpeg')

        category = article.find('.meta-cat a', first=True).text
        entry.category({'term': category, 'label': category})

        entry.title(title)

        description = article.find('.entry-summary', first=True).text
        entry.description(description)

        audio_url = await _get_audio_url(article_url)
        if audio_url is not None:
            entry.link(href=audio_url, rel='voice-audio')

        entries.append(entry)

    return entries


async def generate_feed(
    jlpt_level,
    entry_limit=None,
    return_content_only=False,
):
    fg = FeedGenerator()
    fg.id(f'http://watanoc.com/tag/{jlpt_level}')
    fg.title(f'和タのＣ {jlpt_level}')
    fg.language('ja')

    entries = []
    current_page = 1
    while entry_limit is None or entry_limit > 0:
        page_url = (
                f'http://watanoc.com/tag/{jlpt_level}/page/{current_page}')
        print(page_url)
        session = AsyncHTMLSession()
        r = await session.get(page_url, timeout=20)

        entries_added = await _add_entries_from_page(
            page_url, r, fg, jlpt_level)

        if entries_added:
            entries.extend(entries_added)
            await session.close()

        if entries_added and entry_limit is not None:
            entry_limit -= len(entries_added)
        elif not entries_added:
            break

        current_page += 1

    if return_content_only:
        html = ''
        for entry in reversed(entries):
            title = entry.title()
            content = entry.content()['content']
            html += f'<h1>{title}</h1>{content}'
        return html

    if fg.entry() == 0:
        raise Exception("Generated zero feed entries.")

    return fg.atom_str(pretty=True, encoding='utf-8')
