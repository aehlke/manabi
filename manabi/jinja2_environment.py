from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.utils import translation
from jinja2 import Environment
from allauth.socialaccount.templatetags.socialaccount import get_providers
from allauth.account.utils import user_display


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
        'get_providers': get_providers,
        'user_display': user_display,
    })

    env.install_gettext_translations(translation)

    return env
