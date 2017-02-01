from adminsortable.admin import SortableAdmin
from django.contrib import admin
from django.core import urlresolvers

from manabi.apps.featured_decks.models import FeaturedDeck
from manabi.apps.flashcards.models import Deck


@admin.register(FeaturedDeck)
class FeaturedDeckAdmin(SortableAdmin):
    model = FeaturedDeck

    list_display = ['item', 'deck']
