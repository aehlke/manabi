# -*- coding: utf-8 -*-

CODE_PAGES = {
    'ascii'   : [(2, 126)], #todo: full-width roman
    'hiragana': [(12352, 12447)],
    'katakana': [(12448, 12543)],
    'kanji'   : [
        (19968, 40879),
        (13312, 19967),
        (131072, 173791),
        (63744, 64255),
        (194560, 195103),
    ],
} #todo: rare kanji too


def _code_page(utf8_char):
    "Gets the code page for a Unicode character from a UTF-8 character."
    uni_val = ord(utf8_char)
    for title, pages_list in CODE_PAGES.items():
        for pages in pages_list:
            if uni_val >= pages[0] and uni_val <= pages[1]:
                return title


def is_hiragana(char):
    return _code_page(char) == 'hiragana'


def is_kana(char):
    return (
        _code_page(char) in ['hiragana', 'katakana']
        or char in u'ヶァィェォゥ'
    )


def is_kanji(char):
    return _code_page(char) == 'kanji'
