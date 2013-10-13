from functools import wraps

from django.conf.urls import *
from django.conf import settings
from django.core.urlresolvers import reverse

from manabi.apps.utils.views import direct_to_template
from manabi.apps.flashcards.views.crud import deck_create
from manabi.apps.utils.urldecorators import decorated_patterns


def popup_base_template(func):
    def wrapped(request, *args, **kwargs):
        request.fragment_base_template_name = 'popup_base.html'
        return func(request, *args, **kwargs)
    return wraps(func)(wrapped)


fact_creator_urlpatterns = decorated_patterns(
    'manabi.apps.popups.views', popup_base_template,

    url(r'^decks/$', 'deck_chooser',
        name='popups-deck_chooser'),

    url(r'^decks/(?P<deck_id>\d+)/$', 'fact_add_form',
        name='popups-fact_add_form'),

    url(r'^create-deck/$', deck_create, kwargs={
            'cancel_redirect': 'popups-deck_chooser',
            'post_save_redirect': 'popups-deck_chooser',
        }, name='popups-create_deck'),
)


urlpatterns = patterns('manabi.apps.popups.views',
    url(r'^fact-creator/', include(fact_creator_urlpatterns)),
)
