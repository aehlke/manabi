# -*- coding: utf-8 -*-

from manabi.test_helpers import (
    ManabiTestCase,
)
from manabi.apps.furigana.inject import inject_furigana


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
        text_with_furigana = inject_furigana(ascii_text)
        self.assertEqual(ascii_text, text_with_furigana)

    def test_expression_with_kanji(self):
        text_with_furigana = inject_furigana(u"背を寄せる")
        import sys
        print >>sys.stderr,"Injected: ", text_with_furigana
        print >>sys.stderr, u"｜背《せ》を｜寄《よ》せる"
        self.assertEqual(u"｜背《せ》を｜寄《よ》せる", text_with_furigana)
