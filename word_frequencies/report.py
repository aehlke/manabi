# -*- coding: utf-8 -*-

EXCEPTIONS = [
    u'の',
    u'た',
    u'に',
    u'は',
    u'て',
    u'を',
    u'だ',
    u'が',
    u'と',
    u'も',
    u'よ',
    u'ね',
    u'へ',
    u'で',
    u'じゃ',
    u'さん',
    u'・',
]

print('# -*- coding: utf-8 -*-')
print()
print('WORD_FREQUENCIES = {')
for l in open('word_freq_report.txt').readlines():
    freq, word, _, __, ___ = l.split()

    if word.decode('utf8') in EXCEPTIONS:
        continue

    print('    u"{}": {},'.format(word, freq))
print('}')
