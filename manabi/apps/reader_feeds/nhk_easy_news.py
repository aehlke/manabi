# -*- encoding: utf-8 -*-
import re
from datetime import datetime
from urllib.parse import urlparse, urlunparse, urljoin

import lxml.html
import feedparser
import praw
from django.conf import settings
from feedgen.feed import FeedGenerator
from lxml.cssselect import CSSSelector
from requests_html import HTMLSession


ENTRY_COUNT = 18


def _get_image_url(response, nhk_url):
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
            style = (
                response.html
                .find('#nPlayerContainerAltContentPosterFrame div', first=True)
                .attrs.get('style')
            )
        except AttributeError:
            return None
        src = style.split('("', 1)[1].split('")')[0]

    # Parse the image URL with stdlib.
    parsed = urlparse(src)._asdict()

    # If link is relative, then join it with base_url.
    if not parsed['netloc']:
        return urljoin(response.html.url, src)

    # Link is absolute; if it lacks a scheme, add one from base_url.
    if not parsed['scheme']:
        parsed['scheme'] = urlparse(response.html.url).scheme

        # Reconstruct the URL to incorporate the new scheme.
        parsed = (v for v in parsed.values())
        return urlunparse(parsed)

    # Link is absolute and complete with scheme; nothing to be done here.
    return src


def _get_comments(reddit, post):
    '''
    Returns (comments URL, comment count)
    '''
    post_id = re.search(r'comments/(.+?)/', post.link).groups()[0]
    submission = reddit.submission(id=post_id)
    return (post.link, submission.num_comments)


def _inject_comments(reddit, post, content):
    comments_url, comments_count = _get_comments(reddit, post)

    if comments_count == 0:
        return content

    content = (
         '<p><a href="{}" target="_blank">{} translation comment{}</a></p>'
        .format(
            comments_url, comments_count, 's' if comments_count > 1 else '')
    ) + content

    return content

def _clean_content(content):
    trees = lxml.html.fragments_fromstring(content)
    content_tree = [tree for tree in trees if tree.get('class') == 'md'][0]

    # Remove URL and blank line.
    for _ in range(2):
        content_tree.remove(content_tree[0])

    # Remove bot signature.
    for _ in range(2):
        content_tree.remove(content_tree[-1])

    return lxml.html.tostring(
        content_tree, pretty_print=True, encoding='unicode')


def generate_nhk_easy_news_feed():
    feed_items = []

    fg = FeedGenerator()
    fg.id('https://www.reddit.com/r/NHKEasyNews')
    fg.title('NHK Easy News')
    fg.language('ja')

    feed = feedparser.parse(
        'https://www.reddit.com/r/NHKEasyNews.rss?limit={}'.format(ENTRY_COUNT))

    reddit = praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        username=settings.REDDIT_CLIENT_USERNAME,
        password=settings.REDDIT_CLIENT_PASSWORD,
        user_agent='Manabi Reader',
    )

    for post in reversed(feed.entries):
        if 'discord server' in post.title.lower():
            continue

        content = post.content[0].value

        nhk_url_match = re.search(
            r'(http://www3.nhk.or.jp/news/easy/.*?\.html)', content)
        if nhk_url_match is None:
            continue
        nhk_url = nhk_url_match.group()

        session = HTMLSession()
        r = session.get(nhk_url)
        r.html.render()

        image_url = _get_image_url(r, nhk_url)

        cleaned_content = _clean_content(content)

        if image_url is not None:
            cleaned_content = (
                '<p><img src="{}" /></p>'.format(image_url) + cleaned_content)

        cleaned_content = _inject_comments(
            reddit, post, cleaned_content)

        cleaned_content = '<article class="article">{}</article>'.format(
            cleaned_content)

        entry = fg.add_entry()
        entry.id(post.link)
        entry.link({'href': nhk_url})
        entry.title(post.title)

        entry.summary(cleaned_content)
        #TODO: entry.published()
        entry.content(cleaned_content, type='CDATA')

    if fg.entry() == 0:
        raise Exception("Generated zero feed entries from NHK Easy News.")

    return fg.atom_str(pretty=True, encoding='utf-8')
