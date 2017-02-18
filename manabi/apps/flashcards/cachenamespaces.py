from numbers import Number


def fact_grid_namespace(deck_pk):
    '''
    This namespace is keyed on the deck PK. Used for the fact grid.
    '''
    return ['fact_grid', str(deck_pk)]




###############################################################################
# Per-deck, review-related stat caches

def deck_review_stats_namespace(obj):
    '''
    Namespace keyed on the deck PK.

    Invalidated by things like a card being reviewed, or a card being deleted.
    New cards do not affect this namespace, since most stats are unrelated to
    the number of new cards. For the stats which are related to that, use
    a different caching strategy than what this namespace provides.

    `obj` can be a Deck, Card, or deck ID.
    '''
    pk = None

    from manabi.apps.flashcards.models.cards import Card
    from manabi.apps.flashcards.models.decks import Deck

    if isinstance(obj, Number):
        pk = obj
    elif isinstance(obj, Card):
        pk = obj.deck.pk
    elif isinstance(obj, Deck):
        pk = obj.pk

    return ['deck_review_stats', pk]
