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
        ascii_text = 'foo bar'
        text_with_furigana = self.api.inject_furigana(ascii_text)
        self.assertEqual(ascii_text, text_with_furigana)

    def test_expression_with_kanji(self):
        text_with_furigana = self.api.inject_furigana("背を寄せる")
        self.assertEqual("｜背《せ》を｜寄《よ》せる", text_with_furigana)


class FuriganaInjectionTest(ManabiTestCase):
    def test_plain_ascii_text(self):
        ascii_text = 'foo bar'
        text_with_furigana, _ = inject_furigana(ascii_text)
        self.assertEqual(ascii_text, text_with_furigana)

    def test_expression_with_kanji(self):
        text_with_furigana, _ = inject_furigana("背を寄せる")
        self.assertEqual("｜背《せ》を｜寄《よ》せる", text_with_furigana)

    def test_furigana_positions_with_kanji(self):
        _, furigana_positions = inject_furigana("背を寄せる")

        se_kanji = furigana_positions[0]
        self.assertEqual(se_kanji[FURIGANA_POSITION_START], 0)
        self.assertEqual(se_kanji[FURIGANA_POSITION_END], 1)
        self.assertEqual(se_kanji[FURIGANA_POSITION_FURIGANA], "せ")

        yoseru_kanji = furigana_positions[1]
        self.assertEqual(yoseru_kanji[FURIGANA_POSITION_START], 2)
        self.assertEqual(yoseru_kanji[FURIGANA_POSITION_END], 3)
        self.assertEqual(yoseru_kanji[FURIGANA_POSITION_FURIGANA], "よ")

    def test_kanji_and_ascii(self):
        text_with_furigana, _ = inject_furigana("学びfoobar学び")
        self.assertEqual("｜学《まな》びfoobar｜学《まな》び", text_with_furigana)

    def test_furigana_positions_with_kanji_and_ascii(self):
        _, furigana_positions = inject_furigana("学びfoobar学び")

        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_START], 0)
        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_END], 1)
        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_FURIGANA], "まな")

        self.assertEqual(furigana_positions[1][FURIGANA_POSITION_START], 8)
        self.assertEqual(furigana_positions[1][FURIGANA_POSITION_END], 9)
        self.assertEqual(furigana_positions[1][FURIGANA_POSITION_FURIGANA], "まな")

    def test_kanji_and_ascii_spaces(self):
        text_with_furigana, _ = inject_furigana("foobar   学び")
        self.assertEqual("foobar   ｜学《まな》び", text_with_furigana)

    def test_furigana_positions_with_kanji_and_ascii_spaces(self):
        _, furigana_positions = inject_furigana("foobar   学び")

        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_START], 9)
        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_END], 10)
        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_FURIGANA], "まな")

    def test_furigana_positions_with_kanji_and_hiragana_prefix_and_ascii_spaces(self):
        _, furigana_positions = inject_furigana("foo   で背を寄せる")

        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_START], 7)
        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_END], 8)
        self.assertEqual(furigana_positions[0][FURIGANA_POSITION_FURIGANA], "せ")
