import itertools

from django.contrib.auth import get_user_model
from django.db.models import prefetch_related_objects, Prefetch


BULK_BATCH_SIZE = 2000


def _subscriber_decks_already_with_facts(subscriber_decks, facts):
    from manabi.apps.flashcards.models import Fact

    return set(Fact.objects.filter(
        deck__in=subscriber_decks,
        synchronized_with__in=facts,
    ).values_list('deck_id', 'synchronized_with_id'))


def _subscriber_deck_already_has_fact(
    subscriber_deck_id,
    shared_fact,
    subscriber_decks_already_with_facts,
):
    return (
        (subscriber_deck_id, shared_fact.id) in
        subscriber_decks_already_with_facts
    )


def _copy_facts_to_subscribers(facts, subscribers):
    '''
    The meat-and-potatoes of the copy operation.
    '''
    from manabi.apps.flashcards.models import Card, Fact, Deck

    shared_deck = facts[0].deck
    subscriber_decks = shared_deck.subscriber_decks.filter(
        owner__in=subscribers,
        active=True,
    )
    subscriber_deck_values = subscriber_decks.values_list('id', 'owner_id')
    subscriber_decks_already_with_facts = (
        _subscriber_decks_already_with_facts(subscriber_decks, facts)
    )

    fact_cards_prefetch = Prefetch(
        'card_set',
        queryset=Card.objects.filter(active=True, suspended=False),
        to_attr='available_cards',
    )
    try:
        facts = (
            facts.filter(active=True)
            .prefetch_related(fact_cards_prefetch)
        )
    except AttributeError:
        facts = [fact for fact in facts if fact.active]
        prefetch_related_objects(facts, fact_cards_prefetch)

    copied_facts = []
    copied_cards = []
    updated_subscriber_deck_ids = set()
    for shared_fact in facts:
        copy_attrs = [
            'active', 'suspended', 'new_fact_ordinal',
            'expression', 'reading', 'meaning', 'example_sentence',
            'jmdict_id',
        ]
        fact_kwargs = {attr: getattr(shared_fact, attr) for attr in copy_attrs}

        for subscriber_deck_id, subscriber_id in subscriber_deck_values:
            if _subscriber_deck_already_has_fact(
                subscriber_deck_id,
                shared_fact,
                subscriber_decks_already_with_facts,
            ):
                continue

            fact = Fact(
                deck_id=subscriber_deck_id,
                synchronized_with=shared_fact,
                **fact_kwargs
            )
            copied_facts.append(fact)

            # Copy the cards.
            copied_cards_for_fact = []
            for shared_card in shared_fact.available_cards:
                card = shared_card.copy(fact, owner_id=subscriber_id)
                copied_cards_for_fact.append(card)
            copied_cards.append(copied_cards_for_fact)

            updated_subscriber_deck_ids.add(subscriber_deck_id)

    # Persist everything.
    created_facts = Fact.objects.bulk_create(
        copied_facts, batch_size=BULK_BATCH_SIZE)
    for fact, fact_cards in zip(created_facts, copied_cards):
        for fact_card in fact_cards:
            fact_card.fact_id = fact.id
    Card.objects.bulk_create(
        itertools.chain.from_iterable(copied_cards),
        batch_size=BULK_BATCH_SIZE)

    # Refresh denormalized card count.
    for subscriber_deck_id in updated_subscriber_deck_ids:
        Deck.objects.filter(id=subscriber_deck_id).update(
            card_count=Card.objects.filter(
                deck_id=subscriber_deck_id,
            ).available().count(),
        )


def copy_facts_to_subscribers(facts, subscribers=None):
    '''
    Only call this with facts of the same deck.

    If facts already exist in subscriber decks, this will skip them for those
    decks. It will not resynchronize their contents if they happen to be stale.

    If `subscribers` is `None`, it will copy to all subscribers of the facts'
    decks.
    '''
    if not facts:
        return

    if not all(fact.deck_id is not None for fact in facts):
        raise ValueError("Facts must be saved first to copy them.")
    if len({fact.deck_id for fact in facts}) != 1:
        raise ValueError("Can only copy facts from the same deck.")

    deck = facts[0].deck

    if not deck.shared:
        raise TypeError("Facts cannot be copied from an unshared deck.")

    if subscribers is None:
        subscribers = get_user_model().objects.filter(
            pk__in=deck.subscriber_decks.values_list('owner'))

    _copy_facts_to_subscribers(facts, subscribers=subscribers)
