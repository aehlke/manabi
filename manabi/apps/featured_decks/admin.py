from adminsortable.admin import SortableAdmin
from django.contrib import admin

from manabi.apps.featured_decks.models import FeaturedDeck
from manabi.apps.flashcards.models import Deck


@admin.register(FeaturedDeck)
class FeaturedDeckAdmin(SortableAdmin):
    model = FeaturedDeck

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'deck':
            kwargs['queryset'] = Deck.objects.shared_decks()

        return super(FeaturedDeckAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
