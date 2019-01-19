# -*- coding: utf-8 -*-

import MeCab
import jcconv
from django.conf import settings

tagger = MeCab.Tagger('-Ochasen')


def _reading(node):
    surface = node.surface
    reading = node.feature.split(',')[-2]
    if reading == '*':
        return None
    reading = jcconv.kata2hira(reading)

    return reading


def inject_furigana(text):
    '''
    Returns 2-tuple of (text_with_furigana, furigana_positions).
    '''
    furigana_positions = []

    injected_text = []
    remaining_text = text
    current_offset = 0

    # https://runble1.com/python-mecab-morphological-analysis/
    tagger.parse('')

    node = tagger.parseToNode(text)
    while node:
        surface = node.surface

        # Add any skipped text.
        node_index_in_remaining_text = remaining_text.find(surface)
        injected_text.append(remaining_text[:node_index_in_remaining_text])
        remaining_text = (
            remaining_text[node_index_in_remaining_text + len(surface):])

        reading = _reading(node)

        # Skip text?
        if (reading is None
                or reading == surface
                or jcconv.hira2kata(reading) == surface):
            injected_text.append(surface)
            current_offset += node_index_in_remaining_text + len(surface)
            node = node.next
            continue

        suffix = ''
        redundant_length = 0
        for surface_char, reading_char in zip(
            reversed(surface), reversed(reading),
        ):
            if surface_char != reading_char:
                break
            redundant_length += 1
        if redundant_length > 0:
            reading = reading[:-redundant_length]
            suffix = surface[-redundant_length:]
            surface = surface[:-redundant_length]

        injected_text.append('｜{}《{}》{}'.format(surface, reading, suffix))

        current_offset += node_index_in_remaining_text
        furigana_positions.append((current_offset, current_offset + len(surface), reading))
        current_offset += len(surface) + len(suffix)

        node = node.next

    injected_text.append(remaining_text)

    return (''.join(injected_text), furigana_positions)
