# -*- coding: utf-8 -*-

from django.conf import settings
import MeCab

tagger = MeCab.Tagger(settings.MECAB_RC_PATH)


def _reading(node):
    node.surface.decode('utf8').split(',')[-2]


def inject_furigana(text):
    injected_text = []

    node = tagger.parseToNode(text.encode('utf8'))
    while node:
        surface = node.surface.decode('utf8')
        reading = _reading(node)

        if reading == node.surface:
            injected_text.append(surface)
        else:
            injected_text.append(u'｜{}《{}》'.format(surface, reading))

        node = node.next

    return u''.join(injected_text)
