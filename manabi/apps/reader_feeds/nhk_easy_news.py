# -*- encoding: utf-8 -*-
import asyncio
import re
from datetime import datetime
from urllib.parse import urlparse, urlunparse, urljoin

import lxml.html
import feedparser
import praw
import requests
from django.conf import settings
from feedgen.feed import FeedGenerator
from lxml.cssselect import CSSSelector
from lxml import etree
from requests_html import AsyncHTMLSession

ENTRY_COUNT = 18


def _get_image_url_from_video(video_url):
    '''
    Can return a relatve URL.
    '''
    json_url = video_url.split('.html')[0] + '.json'
    response = requests.get(json_url)
    if response.status_code == 404:
        return None
    src = response.json()['mediaResource']['posterframe']
    return src


def _absolute_url(response, url):
    # Parse the URL with stdlib.
    parsed = urlparse(url)._asdict()

    # If link is relative, then join it with base_url.
    if not parsed['netloc']:
        return urljoin(response.html.url, url)

    # Link is absolute; if it lacks a scheme, add one from base_url.
    if not parsed['scheme']:
        parsed['scheme'] = urlparse(response.html.url).scheme

        # Reconstruct the URL to incorporate the new scheme.
        parsed = (v for v in parsed.values())
        return urlunparse(parsed)

    # Link is absolute and complete with scheme; nothing to be done here.
    return url


def _get_image_url(response):
    try:
        src = (
            response.html
            .find('#js-article-figure', first=True)
            .find('img', first=True).attrs.get('src')
        )
    except AttributeError:
        src = None

    if src is None:
        try:
            video_url = response.html.find(
                'iframe.video-player-fixed', first=True).attrs.get('src')
            if video_url.startswith('//'):
                video_url = 'http:' + video_url
            src = _get_image_url_from_video(video_url)
        except AttributeError:
            return None

    return _absolute_url(response, src)


async def _get_voice_frame_url(response):
    if not response.html.find('a.toggle-audio'):
        return None

    page = response.html.page

    #await page.click('article-main__date')
    await page.click('a.toggle-audio')
    await page.waitForSelector('.audio-player iframe')

    iframe = await page.querySelector('.audio-player iframe')
    src = await page.evaluate('(iframe) => iframe.src', iframe)
    return _absolute_url(response, src)


def _get_comments(reddit, post):
    '''
    Returns (comments URL, comment count)
    '''
    post_id = re.search(r'comments/(.+?)/', post.link).groups()[0]
    submission = reddit.submission(id=post_id)
    return (post.link, submission.num_comments)


def _add_comments(reddit, post, entry):
    comments_url, comments_count = _get_comments(reddit, post)

    if comments_count == 0:
        return

    plural_suffix = 's' if comments_count > 1 else ''

    entry.link(
        href=comments_url,
        rel='reddit-translations',
        title=f'{comments_count} translation{plural_suffix} on Reddit',
    )


def _article_body_html(response):
    #print(response.html.find('.article-body'))
    article_body = response.html.find('.article-body', first=True).lxml
    for ruby in article_body.cssselect('ruby'):
        ruby.remove(ruby.find('rt'))
    etree.strip_tags(article_body, 'ruby', 'span', 'a')
    return etree.tostring(article_body).decode('utf-8')


async def _process_and_add_entry(post, nhk_url, response, fg, reddit):
    content = _article_body_html(response)

    image_url = _get_image_url(response)
    if image_url is not None:
        content = (
            '<p><img src="{}" /></p>'.format(image_url) + content)

    content = f'<article class="article">{content}</article>'

    entry = fg.add_entry()
    entry.id(post.link)
    entry.link({'href': nhk_url})
    entry.title(post.title)
    entry.link(href=image_url, rel='enclosure', type='image/jpeg')

    #TODO: entry.published()
    entry.content(content, type='CDATA')

    _add_comments(reddit, post, entry)

    voice_frame_url = await _get_voice_frame_url(response)
    if voice_frame_url is not None:
        entry.link(href=voice_frame_url, rel='voice-frame')

    return entry


async def generate_nhk_easy_news_feed(
    entry_count=ENTRY_COUNT,
    return_content_only=False,
):
    feed_items = []

    fg = FeedGenerator()
    fg.id('https://www.reddit.com/r/NHKEasyNews')
    fg.title('NHK Easy News')
    fg.language('ja')

    feed = feedparser.parse(
        'https://www.reddit.com/r/NHKEasyNews.rss?limit={}'
        .format(entry_count))

    reddit = praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        username=settings.REDDIT_CLIENT_USERNAME,
        password=settings.REDDIT_CLIENT_PASSWORD,
        user_agent='Manabi Reader',
    )

    entries = []
    for post in reversed(feed.entries):
        if 'discord server' in post.title.lower():
            continue

        reddit_content = post.content[0].value
        nhk_url_match = re.search(
            r'(http://www3.nhk.or.jp/news/easy/.*?\.html)', reddit_content)
        if nhk_url_match is None:
            continue
        nhk_url = nhk_url_match.group()

        session = AsyncHTMLSession()
        r = await session.get(nhk_url, timeout=60)
        await r.html.arender(keep_page=True)

        entry = await _process_and_add_entry(
            post, nhk_url, r, fg, reddit)
        entries.append(entry)

        #r.html.page.close()
        await session.close()

        if entry is None:
            continue

    if return_content_only:
        html = ''
        for entry in reversed(entries):
            title = entry.title()
            content = entry.content()['content']
            html += f'<article><h1>{title}</h1>{content}</article>'
        return html


    if fg.entry() == 0:
        raise Exception("Generated zero feed entries from NHK Easy News.")

    return fg.atom_str(pretty=True, encoding='utf-8')
