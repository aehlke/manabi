# -*- coding: utf-8 -*-

from manabi.test_helpers import (
    ManabiTestCase,
)
from manabi.apps.furigana.inject import inject_furigana


FURIGANA_POSITION_START = 0
FURIGANA_POSITION_END = 1
FURIGANA_POSITION_FURIGANA = 2


class FuriganaInjectionAPITest(ManabiTestCase):
    def test_plain_ascii_text(self):
        ascii_text = u'foo bar'
        text_with_furigana = self.api.inject_furigana(ascii_text)
        self.assertEqual(ascii_text, text_with_furigana)

    def test_expression_with_kanji(self):
        text_with_furigana = self.api.inject_furigana(u"背を寄せる")
        self.assertEqual(u"｜背《せ》を｜寄《よ》せる", text_with_furigana)


class FuriganaInjectionTest(ManabiTestCase):
    def test_plain_ascii_text(self):
        ascii_text = u'foo bar'
        text_with_furigana, _ = inject_furigana(ascii_text)
        self.assertEqual(ascii_text, text_with_furigana)

    def test_expression_with_kanji(self):
        text_with_furigana, _ = inject_furigana(u"背を寄せる")
        self.assertEqual(u"｜背《せ》を｜寄《よ》せる", text_with_furigana)

    def test_furigana_positions_with_kanji(self):
        _, furigana_positions = inject_furigana(u"背を寄せる")

        se_kanji = furigana_positions[0]
        self.assertEqual(se_kanji[FURIGANA_POSITION_START], 0)
        self.assertEqual(se_kanji[FURIGANA_POSITION_END], 1)
        self.assertEqual(se_kanji[FURIGANA_POSITION_FURIGANA], u"せ")

        yoseru_kanji = furigana_positions[1]
        self.assertEqual(yoseru_kanji[FURIGANA_POSITION_START], 2)
        self.assertEqual(yoseru_kanji[FURIGANA_POSITION_END], 3)
        self.assertEqual(yoseru_kanji[FURIGANA_POSITION_FURIGANA], u"よ")

    def test_kanji_and_ascii(self):
        text_with_furigana, _ = inject_furigana(u"学びfoobar学び")
        self.assertEqual(u"｜学《まな》びfoobar｜学《まな》び", text_with_furigana)

    def test_furigana_positions_with_kanji_and_ascii(self):
        _, furigana_positions = inject_furigana(u"学びfoobar学び")

        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_START], 0)
        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_END], 1)
        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_FURIGANA], u"まな")

        self.assertEqual(furigana_positions[1][FURIGANA_POSITION_START], 8)
        self.assertEqual(furigana_positions[1][FURIGANA_POSITION_END], 9)
        self.assertEqual(furigana_positions[1][FURIGANA_POSITION_FURIGANA], u"まな")
