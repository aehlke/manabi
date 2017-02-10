from django.contrib import admin

from manabi.apps.books.models import Textbook
from manabi.apps.flashcards.models import (
    Card,
    CardHistory,
    Deck,
    DeckCollection,
    Fact,
)


class CardAdmin(admin.ModelAdmin):
    raw_id_fields = ('fact',)
    list_display = ('__unicode__', 'last_due_at', 'due_at', 'last_reviewed_at',)


class FactAdmin(admin.ModelAdmin):
    raw_id_fields = ('synchronized_with',)
    list_display = ('__unicode__', 'owner',)
    list_filter = ('deck',)
    readonly_fields = ('created_at', 'modified_at',)


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    fields = (
        'name', 'description', 'suspended', 'active', 'image', 'collection',
        'collection_ordinal', 'randomize_card_order',
    )
    raw_id_fields = ('synchronized_with',)
    list_display = ('__unicode__', 'owner', 'synchronized_with')
    list_filter = ('shared',)
    readonly_fields = ('created_at', 'modified_at',)

    def get_queryset(self, request):
        queryset = super(DeckAdmin, self).get_queryset(request)
        return queryset.filter(active=True)


@admin.register(DeckCollection)
class DeckCollectionAdmin(admin.ModelAdmin):
    fields = ('name', 'description', 'image')
    readonly_fields = ('created_at', 'modified_at',)


class TextbookAdmin(admin.ModelAdmin):
    pass


#TODO admin.site.register(Deck, DeckAdmin)
#TODO admin.site.register(CardHistory)
#TODO admin.site.register(Fact, FactAdmin)
#TODO admin.site.register(Card, CardAdmin)
#TODO admin.site.register(Textbook)

