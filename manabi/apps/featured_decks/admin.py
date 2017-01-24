from adminsortable.admin import SortableAdmin
from django.contrib import admin
from django.core import urlresolvers

from manabi.apps.featured_decks.models import FeaturedDeck
from manabi.apps.flashcards.models import Deck


@admin.register(FeaturedDeck)
class FeaturedDeckAdmin(SortableAdmin):
    model = FeaturedDeck

    list_display = ['deck', 'link_to_deck_admin']

    def link_to_deck_admin(self, obj):
        return "WHAT"
        url = urlresolvers.reverse(
            'admin:manabi_deck_change', args=[obj.Deck.id])
        return u'<a href="{}">{}</a>'.format(url, obj.Deck.name)
    link_to_deck_admin.allow_tags = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'deck':
            kwargs['queryset'] = Deck.objects.shared_decks()

        return super(FeaturedDeckAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
