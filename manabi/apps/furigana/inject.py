import MeCab

tagger = MeCab.Tagger()


def inject_furigana(text):
    nodes = tagger.parseToNode(text.encode('utf8'))
    return text
