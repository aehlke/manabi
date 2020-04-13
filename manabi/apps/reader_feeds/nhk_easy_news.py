# -*- encoding: utf-8 -*-
import asyncio
import re
import time
from datetime import datetime
from urllib.parse import urlparse, urlunparse, urljoin

import lxml.html
import feedparser
import praw
import pytz
import requests
from django.conf import settings
from feedgen.feed import FeedGenerator
from lxml import etree
from requests_html import AsyncHTMLSession

ENTRY_COUNT = 30
ATTEMPTS_PER_ENTRY = 15


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


async def _get_voice_audio_url(response):
    news_id = response.html.base_url.split('/')[-2]
    m3u8_url = (
        'https://nhks-vh.akamaihd.net/i/news/easy/{0}.mp4/master.m3u8'
        .format(news_id)
    )
    return m3u8_url


def _get_comments(reddit, reddit_post):
    '''
    Returns (comments URL, comment count)
    '''
    post_id = re.search(r'comments/(.+?)/', reddit_post.link).groups()[0]
    submission = reddit.submission(id=post_id)
    return (reddit_post.link, submission.num_comments)


def _add_comments(reddit, reddit_post, entry):
    comments_url, comments_count = _get_comments(reddit, reddit_post)

    if comments_count == 0:
        return

    plural_suffix = 's' if comments_count > 1 else ''

    entry.link(
        href=comments_url,
        rel='reddit-translations',
        title=f'{comments_count} Translation{plural_suffix} on Reddit',
    )


class NoArticleBodyError(ValueError):
    pass


def _article_body_html(response):
    try:
        article_body = response.html.find('.article-body', first=True).lxml
    except AttributeError:
        raise NoArticleBodyError()
    for ruby in article_body.cssselect('ruby'):
        ruby.remove(ruby.find('rt'))
    etree.strip_tags(article_body, 'ruby', 'span', 'a')
    # For some reason, article_body gets wrapped in <html/>
    return etree.tostring(article_body[0], method='html').decode('utf-8')


def _post_date(raw_nhk_json_date):
    dt = datetime.strptime(raw_nhk_json_date, '%Y-%m-%d %H:%M:%S')
    return pytz.timezone('Asia/Tokyo').localize(dt)


async def _process_and_add_entry(
    nhk_post_json, response, fg, reddit, reddit_posts,
):
    content = _article_body_html(response)

    entry = fg.add_entry()

    image_url = _get_image_url(response)
    if image_url is not None:
        content = (
            '<p><img src="{}" /></p>'.format(image_url) + content)
        entry.link(href=image_url, rel='enclosure', type='image/jpeg')

    content = f'<article class="article">{content}</article>'

    entry.id(nhk_post_json['news_web_url'])
    entry.link({'href': nhk_post_json['news_web_url']})

    entry.title(nhk_post_json['title'])
    entry.published(_post_date(nhk_post_json['news_prearranged_time']))

    #TODO: entry.published()
    entry.content(content, type='CDATA')

    reddit_post = reddit_posts.get(nhk_post_json['news_web_url'])
    if reddit_post is not None:
        _add_comments(reddit, reddit_post, entry)

    voice_audio_url = await _get_voice_audio_url(response)
    if voice_audio_url is not None:
        entry.link(href=voice_audio_url, rel='voice-audio')

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

    # https://stackoverflow.com/a/57637827/89373
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

    reddit_feed = feedparser.parse(
        'https://www.reddit.com/r/NHKEasyNews.rss?limit={}'
        .format(entry_count))
    if reddit_feed.get('bozo') == 1:
        raise Exception(reddit_feed.get('bozo_exception'))

    reddit = praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        username=settings.REDDIT_CLIENT_USERNAME,
        password=settings.REDDIT_CLIENT_PASSWORD,
        user_agent='Manabi Reader',
    )

    nhk_json_url = 'https://www3.nhk.or.jp/news/easy/news-list.json'
    nhk_json_response = requests.get(nhk_json_url)
    nhk_json_response.raise_for_status()
    nhk_json = nhk_json_response.json()

    reddit_posts = {}
    for reddit_post in reversed(reddit_feed.entries):
        if 'discord server' in reddit_post.title.lower():
            continue

        reddit_content = reddit_post.content[0].value
        nhk_url_match = re.search(
            r'(http://www3.nhk.or.jp/news/easy/.*?\.html)', reddit_content)
        if nhk_url_match is None:
            continue
        nhk_post_url = nhk_url_match.group()
        nhk_post_url = nhk_post_url.replace('http://', 'https://', 1)

        reddit_posts[nhk_post_url] = reddit_post

    entries = []
    for nhk_posts in [nhk_json[0][key] for key in sorted(nhk_json[0].keys())]:
        for nhk_post_json in sorted(
            nhk_posts, key=lambda x: x['news_prearranged_time']
        ):
            nhk_post_url = nhk_post_json['news_web_url']

            for attempt in range(ATTEMPTS_PER_ENTRY):
                session = AsyncHTMLSession()
                r = await session.get(nhk_post_url, timeout=60)
                await r.html.arender(keep_page=True)

                try:
                    entry = await _process_and_add_entry(
                        nhk_post_json, r, fg, reddit, reddit_posts)
                except NoArticleBodyError:
                    if attempt < ATTEMPTS_PER_ENTRY - 1:
                        time.sleep(1)
                        continue
                    raise

                if entry is not None:
                    entries.append(entry)

                    #r.html.page.close()
                    await session.close()
                    break

            if entry is None:
                continue

            if entry is not None and entry_count is not None:
                entry_count -= 1

                if entry_count <= 0:
                    break

        if entry_count <= 0:
            break

    if return_content_only:
        html = ''
        for entry in reversed(entries):
            title = entry.title()
            content = entry.content()['content']
            html += f'<h1>{title}</h1>{content}'
        return html

    if fg.entry() == 0:
        raise Exception("Generated zero feed entries from NHK Easy News.")

    return fg.atom_str(pretty=True, encoding='utf-8')
