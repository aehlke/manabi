# -*- coding: utf-8 -*-

import re

from django.utils.html import escape


def as_ruby_tags(value):
    '''
    Expects a "Manabi raw" format string as input.
    '''
    return re.sub(
        ur'｜([^《》｜]*)《([^《》｜]*)》',
        ur'<ruby>\1<rt>\2</rt></ruby>',
        escape(value),
        re.UNICODE)
