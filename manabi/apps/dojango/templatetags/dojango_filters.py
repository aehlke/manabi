from django.template import Library

from manabi.apps.dojango.util import json_encode

register = Library()

@register.filter
def json(input):
    return json_encode(input)
