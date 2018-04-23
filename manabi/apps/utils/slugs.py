# Thanks, Armin Ronacher.

import re
from unidecode import unidecode

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.:]+')


def slugify(text, delim='-', max_length=50):
    '''Generates an ASCII-only slug.'''
    def join(words):
        return str(delim.join(words))

    result = []
    for word in _punct_re.split(text.lower()):
        new_result = result + unidecode(word).split()
        if len(join(new_result)) <= max_length:
            result = new_result
        else:
            break

    return join(result)


