from django import template

register = template.Library()

from re import compile, UNICODE



#RUBY_TEXT_MARKUP_TEMPLATE = u'<ruby><rb>{expression}</rb><rp>(</rp><rt>{reading}</rt><rp>)</rp></ruby>'
RUBY_TEXT_MARKUP_TEMPLATE = '<span class="ezRuby" title="{reading}">{expression}</span>'

#_LEFT_CARET = u'\&lt;'
#_RIGHT_CARET = u'\&gt;'

#ruby_prog = compile(u'\&lt;(.*)\|(.*)\&gt;')
#unescaped_ruby_prog = compile(u'<(.*)\|(.*)>')
#ruby_prog = compile(u'\s(.*)\[(.*)\]', UNICODE) #for some reason, only [\s^] works, and [^\s] doesn't - so [] must prefer the first option it's given over the second
ruby_prog = compile('\s?(\S*?)\[(.*?)\]', UNICODE) #for some reason, only [\s^] works, and [^\s] doesn't - so [] must prefer the first option it's given over the second
#ruby_prog2 = compile(u'^(.*)\[(.*)\]', UNICODE)
#unescaped_ruby_prog = compile(u'[^\s](.*)\[(.*)\]')

def furiganaize(text):
    new_text = ''
    last_match_end = 0

    for match in ruby_prog.finditer(text):
        expression, reading = match.group(1, 2)
        start, end = match.start(), match.end()
        new_substring = RUBY_TEXT_MARKUP_TEMPLATE.format(expression=expression, reading=reading)
        new_text += text[last_match_end:start] + new_substring
        last_match_end = end

    new_text += text[last_match_end:]

    return new_text

#TODO-OLD move below into some other module
def strip_ruby_text(text):
    new_text = ''
    last_match_end = 0
    for match in ruby_prog.finditer(text):
        expression = match.group(1)
        start, end = match.start(), match.end()
        new_substring = expression
        new_text += text[last_match_end:start] + new_substring
        last_match_end = end
    new_text += text[last_match_end:]
    return new_text

def strip_ruby_bottom(text):
    '''
    Returns this field's content, with just the ruby text instead of
    what's beneath it, and the other text.
    <TA|ta>beru becomes taberu
    '''
    new_text = ''
    last_match_end = 0
    for match in ruby_prog.finditer(text):
        reading = match.group(2)
        start, end = match.start(), match.end()
        new_substring = reading
        new_text += text[last_match_end:start] + new_substring
        last_match_end = end
    new_text += text[last_match_end:]
    return new_text


        

@register.tag(name="furiganaize")
def do_furiganaize(parser, token):
    nodelist = parser.parse(('endfuriganaize',))
    parser.delete_first_token()
    return FuriganaizeNode(nodelist)

class FuriganaizeNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        #convert everything of the form <kanji|kana> to kanji with CSS ruby text

        return furiganaize(output)

