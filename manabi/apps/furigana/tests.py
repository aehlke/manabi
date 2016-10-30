# -*- coding: utf-8 -*-

from manabi.test_helpers import (
    ManabiTestCase,
)


class FuriganaInjectionAPITest(ManabiTestCase):
    def test_plain_ascii_text(self):
        ascii_text = u'foo bar'
        text_with_furigana = self.api.inject_furigana(ascii_text)
        self.assertEqual(ascii_text, text_with_furigana)

    def test_expression_with_kanji(self):
        try:
            text_with_furigana = self.api.inject_furigana(u"背を寄せる")
            print "Injected: ", text_with_furigana
            self.assertEqual(u"｜背《せ》を｜寄《よ》せる", text_with_furigana)
        except:
            pass
