# -*- coding: utf-8 -*-
# Generated by Django 1.11a1 on 2017-02-05 22:09
from __future__ import unicode_literals

import json
import re
from os.path import commonprefix

from django.db import migrations


symbols = {'～', '[', ']'}


def strip_reading(reading):
    return re.sub(r'《.*?》', r'', reading.replace('｜', ''))


def make_ruby(kana, kanji):
    from manabi.apps.utils.japanese import is_kana, is_hiragana, is_kanji

    # print u'make ruby [{}], [{}]'.format(kana, kanji)

    if kanji == '一ヶ月':
        return "｜一ヶ月《いっかげつ》"
    elif kanji == 'ユダヤ人':
        return "ユダヤ｜人《じん》"
    elif kanji == '百パーセント':
        return "｜百《ひゃく》パーセント"
    elif kanji == 'ソ連':
        return "ソ｜連《れん》"
    elif kanji == 'キリスト教':
        return "キリスト｜教《きょう》"
    elif kanji == 'Tシャツ':
        return kanji
    elif kanji == '東南アジア':
        return "｜東南《とうなん》アジア"
    elif kanji == '生クリーム':
        return "｜生《なま》クリーム"
    elif kanji == 'スキー場':
        return "スキー｜場《じょう》"
    elif kanji == '〜に比べて':
        return "〜に｜比《くら》べて"

    if ',' in kana and ',' not in kanji:
        kana = kana.replace(',', u'／')
    elif ',' in kana and ',' in kanji:
        kanji1, kanji2 = kanji.split(',')
        kana1, kana2 = kana.split(',')
        return u'{}, {}'.format(
            make_ruby(kana1.strip(), kanji1.strip()),
            make_ruby(kana2.strip(), kanji2.strip()))
    elif ',' in kanji:
        kanji1, kanji2 = kanji.split(',')
        return u'{}, {}'.format(
            make_ruby(kana, kanji1.strip()), make_ruby(kana, kanji2.strip()))

    if kana[-4:] == kanji[-4:] == u'(する)':
        return make_ruby(kana[:-4], kanji[:-4]) + u'（する）'
    elif kana[:3] == kanji[:3] == u'(お)':
        return u'（お）' + make_ruby(kana[3:], kanji[3:])

    # e.g. 取り敢えず, 一ヶ月, 生き生き
    for idx, c in enumerate(kanji):
        if is_kanji(c):
            continue
        if is_kana(c):
            if any(is_kanji(c2) for c2 in kanji[idx + 1:]):
                to_split = c
                if to_split == u'ヶ':
                    to_split = u'っか'
                kana1, kana2 = kana.split(to_split, 1)
                kana1 = kana1 + to_split
                assert kana1 != ''
                return make_ruby(kana1, kanji[:idx + 1]) + make_ruby(kana2, kanji[idx + 1:])
            break

    if all(is_kana(c) for c in kanji):
        return kanji

    if (
        (
            set(kana) & symbols
            or set(kanji) & symbols
            or any((not is_kana(c) and c not in ['/', u'／']) for c in kana)
        )
        and not (kana[:1] == kanji[:1] == u'～')
        and not (kana[-1] == kanji[-1] == u'～')
    ):
        if not kanji:
            return kana
        print kana[:-4], kanji[:-4], (kana[:-4] == kanji[:-4] == u'(する)')
        raise ValueError("Contains symbols: {} {}.".format(kana, kanji))

    if not kanji:
        return kana

    prefix = commonprefix([kana, kanji])
    suffix = commonprefix([kana.split(u'／', 1)[0][::-1], kanji[::-1]])[::-1]
    middle_kanji = kanji[len(prefix):(-len(suffix) or None)]
    if u'／' in kana:
        kana1, kana2 = kana.split(u'／')
        furigana = kana1[len(prefix):(-len(suffix) or None)]
        furigana += kana2[len(prefix):(-len(suffix) or None)]
    else:
        furigana = kana[len(prefix):(-len(suffix) or None)]

    for c in middle_kanji:
        if is_kana(c):
            print prefix, ',', middle_kanji, ',', suffix, ',', furigana
            raise ValueError(
                "Non-simple kanji can't be autoconverted: {}".format(kanji))

    return "{}｜{}《{}》{}".format(prefix, middle_kanji, furigana, suffix)

# TODO: check 生じる
# TODO: check いったん
# TODO: check 生き生き

def swap_encoding(j):
    for note in j:
        for key in note:
            try:
                note[key] = unicode(note[key].decode('unicode-escape'))
            except (AttributeError, UnicodeEncodeError, UnicodeDecodeError):
                pass
            if isinstance(note[key], basestring):
                note[key] = unicode(note[key])
    return j


def forwards(apps, schema_editor):
    from manabi.apps.flashcards.models.constants import (
        PRODUCTION,
        RECOGNITION,
        KANJI_READING,
        KANJI_WRITING,
    )

    Card = apps.get_model('flashcards', 'Card')
    Fact = apps.get_model('flashcards', 'Fact')
    Deck = apps.get_model('flashcards', 'Deck')
    DeckCollection = apps.get_model('flashcards', 'DeckCollection')
    User = apps.get_model('auth', 'User')

    with open('manabi/apps/flashcards/migrations/manabi-4k.json') as f:
        data = swap_encoding(json.loads(f.read()))

    owner = User.objects.get(username='alex')
    collection = DeckCollection.objects.create(
        name='Core 4000',
        description="Learn vocab in the most productive order possible: these decks divide up the top 4000 most common Japanese words, sorting them by the frequency that they appear in a wide range of native materials. The fastest way to achieve literacy is by studying the terms you're most likely to run into when you go watch TV and movies or read articles and books, which is what this collection of decks gives you. As you work through these, you'll find your ability to understand native materials steadily rising.",
    )
    deck_1 = Deck.objects.create(
        name='Core 4000 - Level 1',
        description="Learn vocab in the most productive order possible: this deck takes the top 1000 most common Japanese words, sorting them by the frequency that they appear in a wide range of native materials. The fastest way to achieve literacy is by studying the terms you're most likely to run into when you go watch TV and movies or read articles and books, which is what this collection of decks gives you. As you work through these, you'll find your ability to understand native materials steadily rising.",
        owner=owner,
        collection=collection,
        randomize_card_order=False,
    )
    deck_2 = Deck.objects.create(
        name='Core 4000 - Level 2',
        description="Learn vocab in the most productive order possible: this deck takes the 1000th-2000th most common Japanese words, sorting them by the frequency that they appear in a wide range of native materials. The fastest way to achieve literacy is by studying the terms you're most likely to run into when you go watch TV and movies or read articles and books, which is what this collection of decks gives you. As you work through these, you'll find your ability to understand native materials steadily rising.",
        owner=owner,
        collection=collection,
        randomize_card_order=False,
    )
    deck_3 = Deck.objects.create(
        name='Core 4000 - Level 3',
        description="Learn vocab in the most productive order possible: this deck takes the 2000th-3000th most common Japanese words, sorting them by the frequency that they appear in a wide range of native materials. The fastest way to achieve literacy is by studying the terms you're most likely to run into when you go watch TV and movies or read articles and books, which is what this collection of decks gives you. As you work through these, you'll find your ability to understand native materials steadily rising.",
        owner=owner,
        collection=collection,
        randomize_card_order=False,
    )
    deck_4 = Deck.objects.create(
        name='Core 4000 - Level 4',
        description="Learn vocab in the most productive order possible: this deck takes the 3000th-4000th most common Japanese words, sorting them by the frequency that they appear in a wide range of native materials. The fastest way to achieve literacy is by studying the terms you're most likely to run into when you go watch TV and movies or read articles and books, which is what this collection of decks gives you. As you work through these, you'll find your ability to understand native materials steadily rising.",
        owner=owner,
        collection=collection,
        randomize_card_order=False,
    )
    deck_bonus = Deck.objects.create(
        name='Core 4000 - Bonus',
        description="Learn vocab in the most productive order possible: this deck takes the next few hundred most common Japanese words after the first 4000, sorting them by the frequency that they appear in a wide range of native materials. The fastest way to achieve literacy is by studying the terms you're most likely to run into when you go watch TV and movies or read articles and books, which is what this collection of decks gives you. As you work through these, you'll find your ability to understand native materials steadily rising.",
        owner=owner,
        collection=collection,
        randomize_card_order=False,
    )

    for idx, vocab in enumerate(data):
        try:
            reading = make_ruby(vocab['reading'], vocab['expression'])
        except ValueError as e:
            # if 'Reading' in vocab:
            #     reading = vocab['Reading']
            # else:
            print e.message
            raise

        expression = strip_reading(reading)
        meaning = vocab['meaning']

        if idx < 1000:
            deck = deck_1
        elif idx >= 1000 and idx < 2000:
            deck = deck_2
        elif idx >= 2000 and idx < 3000:
            deck = deck_3
        elif idx >= 3000 and idx < 4000:
            deck = deck_4
        else:
            deck = deck_bonus

        fact = Fact.objects.create(
            deck=deck,
            expression=expression,
            reading=reading,
            meaning=meaning,
        )

        templates = [RECOGNITION]

        for template in templates:
            Card.objects.create(
                owner=owner,
                deck=deck,
                fact=fact,
                template=template,
                new_card_ordinal=idx,
            )
            # print expression, reading, meaning, template, '| Deck:', deck.name

class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0044_deck_randomize_card_order'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]
