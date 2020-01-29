# -*- encoding: utf-8 -*-
import asyncio
import io
import os
import subprocess
from datetime import datetime
from tempfile import NamedTemporaryFile

import lxml.html
import pytz
import requests
from django.conf import settings
from django.core.files.storage import default_storage
from feedgen.feed import FeedGenerator
from requests_html import AsyncHTMLSession

ENTRY_COUNT = 30


async def _get_audio_url(article_url):
    session = AsyncHTMLSession()
    r = await session.get(article_url, timeout=20)
    audio_element = r.html.find('audio.wp-audio-shortcode a', first=True)
    if audio_element is not None:
        return audio_element.attrs['href']


def _reencode_mp3(input_path, output_path):
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'panic',
           '-i', input_path, '-c:a', 'libmp3lame', '-b:a', '128k',
           output_path]
    subprocess.call(cmd)


async def _add_entries_from_page(page_url, response, fg):
    entries = []

    for article in response.html.find('main .post-lists a.post-arc'):
        entry = fg.add_entry(order='append')

        title = article.find('h2 span', first=True).text
        entry.title(title)

        published_raw = article.find('.post-date', first=True).text
        published_parsed = (
            datetime.strptime(published_raw, '%Y年%m月%d日')
            .replace(tzinfo=pytz.timezone('Asia/Tokyo')))
        entry.published(published_parsed)

        article_url = article.attrs['href']
        entry.id(article_url)
        entry.link({'href': article_url})

        image_url = article.find('img.wp-post-image', first=True).attrs['src']
        entry.link(href=image_url, rel='enclosure', type='image/jpeg')

        category = article.find('.post-info .icon-cat', first=True).text
        category = category.split(' / ')[0]
        entry.category({'term': category, 'label': category})

        audio_url = await _get_audio_url(article_url)

        if audio_url is not None:
            audio_filename = audio_url.split('/')[-1].split('?_=1')[0]
            audio_path = f'feeds/audio/slow-communication-{audio_filename}'

            if not default_storage.exists(audio_path):
                audio_request = requests.get(audio_url)
                with NamedTemporaryFile() as f:
                    f.write(audio_request.content)
                    audio_temp_path = f.name

                    reencoded_path = audio_temp_path + '.out.mp3'
                    _reencode_mp3(audio_temp_path, reencoded_path)

                    with open(reencoded_path, 'rb') as output_f:
                        default_storage.save(audio_path, output_f)

                    os.remove(audio_temp_path)
                    os.remove(reencoded_path)

            entry.link(
                href=f'https://manabi.io/media/{audio_path}',
                rel='voice-audio')

        entries.append(entry)

    return entries


async def generate_feed(
    entry_limit=ENTRY_COUNT,
    return_content_only=False,
):
    fg = FeedGenerator()
    fg.id('https://slow-communication.jp/')
    fg.title('Slow Communication')
    fg.language('ja')

    entries = []
    current_page = 1
    while entry_limit is None or entry_limit > 0:
        if current_page == 1:
            page_url = 'https://slow-communication.jp/'
        else:
            page_url = (
                f'https://slow-communication.jp/news/?pg={current_page}')
        print(page_url)
        session = AsyncHTMLSession()
        r = await session.get(page_url, timeout=20)

        entries_added = await _add_entries_from_page(
            page_url, r, fg)

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
        for entry in entries:
            title = entry.title()
            html += f'<h1>{title}</h1>'
        return html

    if fg.entry() == 0:
        raise Exception("Generated zero feed entries.")

    return fg.atom_str(pretty=True, encoding='utf-8')
