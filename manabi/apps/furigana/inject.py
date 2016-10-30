# -*- coding: utf-8 -*-

import MeCab
import jcconv
from django.conf import settings

tagger = MeCab.Tagger('-Ochasen') #.format(settings.MECAB_RC_PATH))


def _reading(node):
    surface = node.surface.decode('utf8')
    reading = node.feature.decode('utf8').split(',')[-2]
    if reading == '*':
        return None
    reading = jcconv.kata2hira(reading)

    return reading


def inject_furigana(text):
    injected_text = []
    remaining_text = text

    # https://runble1.com/python-mecab-morphological-analysis/
    tagger.parse('')

    node = tagger.parseToNode(text.encode('utf8'))
    while node:
        surface = node.surface.decode('utf8')

        # Add any skipped text.
        node_index_in_remaining_text = remaining_text.find(surface)
        injected_text.append(remaining_text[:node_index_in_remaining_text])
        remaining_text = remaining_text[node_index_in_remaining_text + len(surface):]

        reading = _reading(node)

        if (reading is None
                or reading == surface
                or jcconv.hira2kata(reading) == surface):
            injected_text.append(surface)
            node = node.next
            continue

        suffix = ''
        redundant_length = 0
        for surface_char, reading_char in zip(reversed(surface), reversed(reading)):
            if surface_char != reading_char:
                break
            redundant_length += 1
        if redundant_length > 0:
            reading = reading[:-redundant_length]
            suffix = surface[-redundant_length:]
            surface = surface[:-redundant_length]

        injected_text.append(u'｜{}《{}》{}'.format(surface, reading, suffix))

        node = node.next

    injected_text.append(remaining_text)

    return u''.join(injected_text)
