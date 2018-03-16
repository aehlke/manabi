# -*- encoding: utf-8 -*-
import re
from datetime import datetime
from urlparse import urljoin

import requests
import lxml.html
import feedparser
from feedgen.feed import FeedGenerator
from lxml.cssselect import CSSSelector


def _get_image_url(page_tree, nhk_url):
    url = CSSSelector('#mainimg img')(page_tree)[0].get('src')
    if not (url.startswith('http://') or url.startswith('https://')):
        url = urljoin(nhk_url, url)
    return url


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

    feed = feedparser.parse('https://www.reddit.com/r/NHKEasyNews.rss')

    for post in reversed(feed.entries):
        if 'discord server' in post.title.lower():
            continue

        content = post.content[0].value
        nhk_url = re.search(
            r'(http://www3.nhk.or.jp/news/easy/.*?\.html)', content).group()

        r = requests.get(nhk_url)
        page_tree = lxml.html.fromstring(r.text)

        image_url = ''#_get_image_url(page_tree, nhk_url)

        cleaned_content = _clean_content(content)

        entry = fg.add_entry()
        entry.id(post.link)
        entry.title(post.title)
        entry.summary(cleaned_content)
        #TODO: entry.published()
        entry.content(cleaned_content)

    return fg.atom_str(pretty=True, encoding='utf-8')
