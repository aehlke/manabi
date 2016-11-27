import json

from allauth.account.utils import user_display
from allauth.socialaccount.templatetags.socialaccount import get_providers
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.utils import translation
from jinja2 import Environment

from manabi.apps.furigana.jinja2 import as_ruby_tags


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'dir': dir,
        'static': staticfiles_storage.url,
        'url': reverse,
        'get_providers': get_providers,
        'user_display': user_display,
        'json': json.dumps,
        'int': int,
    })

    env.filters['as_ruby_tags'] = as_ruby_tags

    env.install_gettext_translations(translation)

    return env
