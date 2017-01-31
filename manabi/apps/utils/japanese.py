import subprocess
import jcconv
from itertools import takewhile

from django.conf import settings


CODE_PAGES = {
    'ascii'   : (2, 126), #todo: full-width roman
    'hiragana': (12352, 12447),
    'katakana': (12448, 12543),
    'kanji'   : (19968, 40879),
} #todo: rare kanji too


def _code_page(utf8_char):
    "Gets the code page for a Unicode character from a UTF-8 character."
    uni_val = ord(utf8_char)
    for title, pages in CODE_PAGES.iteritems():
        if uni_val >= pages[0] and uni_val <= pages[1]:
            return title
    return 'unknown'


def _furiganaize_complex_compound_word(word, reading,
                                       is_at_beginning_of_transliteration=False):
    '''
    for words of format kanji-kana-kanji-kana like hikkosu, kasidasu, etc.
    Don't include leading or trailing kana in the word or reading.
    word should start and end with kanji.
    Returns None if it's not of the proper form.
    '''
    # Make sure it begins and ends with kanji
    if len(word) < 3 or is_kana(word[0]) or is_kana(word[-1]):
        return None

    # Make sure it has hiragana in between the kanji
    if not any(_code_page(char) == 'hiragana' for char in word[1:-1]):
        return None

    prefix_kanji, rest_of_word = _split_by(lambda char: not is_hiragana(char), word)
    postfix_kanji, middle_kana = _split_by(lambda char: not is_hiragana(char), rest_of_word[::-1]) #split from end
    postfix_kanji, middle_kana = postfix_kanji[::-1], middle_kana[::-1]

    # Make sure there is no kanji in between the hiragana
    if not all(is_hiragana(char) for char in middle_kana):
        return None

    # Get the latest part of the reading, excluding the minimal length of kanji at the start/end,
    # which contains the middle hiragana.
    maximal_reading_kana = reading[len(prefix_kanji):-len(postfix_kanji)]
    if maximal_reading_kana == middle_kana:
        kanji_readings = u'', u''
    kanji_readings = maximal_reading_kana.rsplit(middle_kana, 1)
    if len(kanji_readings) != 2:
        return None
    prefix_kanji_reading = reading[:len(prefix_kanji)] + kanji_readings[0]
    postfix_kanji_reading = kanji_readings[1] + reading[-len(postfix_kanji):]

    space_char = u'\u3000'
    return u'{prefix_kanji}[{prefix_kanji_reading}]{middle}{space_char}{postfix_kanji}[{postfix_kanji_reading}]'.format(
            prefix_kanji=prefix_kanji,
            prefix_kanji_reading=prefix_kanji_reading,
            middle=middle_kana,
            space_char=space_char,
            postfix_kanji=postfix_kanji,
            postfix_kanji_reading=postfix_kanji_reading)




def is_hiragana(char):
    return _code_page(char) == 'hiragana'

def is_kana(char):
    return _code_page(char) in ['hiragana', 'katakana']

def _split_by(filter_func, word):
    '''
    Returns a tuple containing the first part of the word that satisfies filter_func,
    followed by the rest of the word.
    '''
    prefix = u''.join([char for char in takewhile(filter_func, word)])
    return (prefix, word[len(prefix):],)


def _furiganaize(word, reading, is_at_beginning_of_transliteration=False):
    '''word=TAberu, reading=taberu returns TA[ta]beru'''

    #sometimes words like taberu come out as taberu instead of ta and beru
    #detect hiragana stems and split them (or just split off duplicate stems)
    #prefix_kana, rest_of_word = _split_by(['hiragana', 'katakana'], word)
    prefix_kana = u''.join([char for char in takewhile(lambda char: _code_page(char) in ['hiragana', 'katakana'], \
            word)])
    postfix_kana = u''.join([char for char in takewhile(lambda char: _code_page(char) in ['hiragana', 'katakana'], \
            word[::-1][:-len(prefix_kana) or None])]) #take from the end
    postfix_kana = postfix_kana[::-1]

    expression_middle = word[len(prefix_kana):-len(postfix_kana) or None]
    kanji_reading = reading[len(prefix_kana):-len(postfix_kana) or None]

    # Check if it's a compound word which has kana in between kanji
    middle_ret = _furiganaize_complex_compound_word(expression_middle, kanji_reading)
    if not middle_ret:
        middle_ret = u'{kanji}[{reading}]'.format(kanji=expression_middle, reading=kanji_reading)

    # \u3000 is a full-width space - necessary if this isn't the start of the transliteration
    space_char = u'\u3000' if not is_at_beginning_of_transliteration or prefix_kana else u''

    return u'{prefix}{space_char}{middle}{postfix}'.format( \
            prefix=prefix_kana, space_char=space_char, middle=middle_ret, postfix=postfix_kana)



def generate_reading(expression):
    expression = expression.encode(settings.MECAB_ENCODING)
    proc = subprocess.Popen('mecab', shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    mecab_output = proc.communicate(expression)[0].decode(settings.MECAB_ENCODING)
    lines = mecab_output.split(u'\n')[:-2] #skip the \nEOS\n

    ret = u''
    for line in lines:
        if line[0] == u',':
            ret += u','
            continue
        elif line[:3] == u'EOS':
            ret += u'\n'
            continue
        elif line[0].strip() == '':
            ret += line[0]
            continue
        fields = line.split(u',')
        word = fields[0].split()[0]

        if len(fields) == 9:
            reading = fields[7]

            # Has kanji and a reading?
            if (jcconv.kata2hira(reading) != word
                    and reading != word
                    and any(_code_page(char) != 'hiragana'
                            and _code_page(char) != 'katakana'
                            for char in word)):

                # The reading comes in as katakana, we want hiragana.
                reading = jcconv.kata2hira(reading)

                ret += _furiganaize(word, reading, not ret)
            else:
                ret += word
        else:
            ret += word
    return ret


if __name__ == '__main__':
    expression = u'\u8cb8\u3057\u51fa\u3057\u3066'
    print generate_reading(expression)
