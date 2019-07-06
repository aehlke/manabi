# -*- coding: utf-8 -*-

from functools import wraps


def _auto_secondary_prompt(f):
    @wraps(f)
    def wrapper(review_availabilities, secondary=False):
        prompt = f(review_availabilities, secondary=secondary)
        if prompt is None:
            return
        if secondary:
            parts = prompt.split(' ')
            if parts[0].lower() in ["we", "we'll", "you", "you'll", "you're"]:
                prompt = ' '.join(parts[:1] + ['also'] + parts[1:])
        return prompt
    return wrapper


def _pluralize_cards(card_count):
    if card_count == 1:
        return 'card'
    return 'cards'


def _pluralize(singular, plural, count):
    if count == 1:
        return singular
    return plural


def _manabi_reader_suffix(review_availabilities):
    if review_availabilities.is_for_manabi_reader:
        return ' from this article'
    return ''


@_auto_secondary_prompt
def _failed_due(review_availabilities, secondary=False):
    '''
    Failed, due.
    '''
    cards = review_availabilities.base_cards_queryset
    count = cards.failed().due().count()
    if count == 0:
        return
    cards_suffix = _manabi_reader_suffix(review_availabilities)
    return (
        f"You're ready to revisit {count} "
        f"{_pluralize_cards(count)}{cards_suffix} "
        f"that you had forgotten."
    )


@_auto_secondary_prompt
def _mature_due(review_availabilities, secondary=False):
    '''
    Mature, due.
    '''
    cards = review_availabilities.base_cards_queryset
    count = cards.mature().due().excluding_failed().count()
    if count == 0:
        return
    cards_suffix = _manabi_reader_suffix(review_availabilities)
    return (
        f"We have {count} {_pluralize_cards(count)}{cards_suffix} "
        f"that you know well but "
        f"may forget if left unused much longer."
    )


# TODO
# def _far_over_due(review_availabilities, secondary=False):
#     '''
#     Far over-due.
#     '''
#     return u"You may have already forgotten {} cards—pick them up again quickly through review."


@_auto_secondary_prompt
def _young_due(review_availabilities, secondary=False):
    '''
    Young, due, excluding failed cards.
    '''
    cards = review_availabilities.base_cards_queryset
    count = cards.young().due().excluding_failed().count()
    if count == 0:
        return
    cards_suffix = _manabi_reader_suffix(review_availabilities)
    return (
        f"You'll soon forget {count} {_pluralize_cards(count)}{cards_suffix} "
        f"you're still learning—reinforce "
        f"{_pluralize('it', 'them', count)} now for maximum effectiveness."
    )


@_auto_secondary_prompt
def _failed_not_due(review_availabilities, secondary=False):
    '''
    Failed, not due.
    '''
    cards = review_availabilities.base_cards_queryset
    count = cards.failed().not_due().count()
    if count == 0:
        return
    cards_suffix = _manabi_reader_suffix(review_availabilities)
    return (
        f"We have {count} {_pluralize_cards(count)}{cards_suffix} you "
        f"forgot last time that you could wait a bit to revisit."
    )


@_auto_secondary_prompt
def _new_under_daily_limit(review_availabilities, secondary=False):
    '''
    Next new cards, under daily limit.
    '''
    if review_availabilities.new_cards_per_day_limit_reached:
        return
    count = review_availabilities.next_new_cards_count
    if count == 0:
        return

    cards_suffix = _manabi_reader_suffix(review_availabilities)

    if review_availabilities.new_cards_limit.learned_today_count > 0:
        return (
            f"We have {count} more new {_pluralize_cards(count)}{cards_suffix}"
            f"for you to learn."
        )
    else:
        return (
            f"We have {count} new {_pluralize_cards(count)}{cards_suffix}"
            f"for you to learn."
        )


@_auto_secondary_prompt
def _new_over_daily_limit(review_availabilities, secondary=False):
    '''
    Next new cards, past daily limit.

    Will never appear as the secondary prompt, since the "learn new cards"
    button does not appear when there are any cards due.
    '''
    if secondary:
        return
    if not review_availabilities.new_cards_per_day_limit_reached:
        return
    count = review_availabilities.next_new_cards_count
    if count == 0:
        return

    already_learned = review_availabilities.new_cards_limit.learned_today_count
    cards_suffix = _manabi_reader_suffix(review_availabilities)
    return (
        f"You've already learned {already_learned} new "
        f"{_pluralize_cards(count)} today, but we have {count} "
        f"more{cards_suffix} if you're feeling ambitious."
    )

@_auto_secondary_prompt
def _new_buried_under_daily_limit(review_availabilities, secondary=False):
    '''
    Buried new cards, under daily limit.
    '''
    if review_availabilities.new_cards_per_day_limit_reached:
        return
    count = review_availabilities.buried_new_cards_count
    if count == 0 or count is None:
        return

    cards_suffix = _manabi_reader_suffix(review_availabilities)
    template = (
        f"We have {count} new {_pluralize_cards(count)}{cards_suffix}, "
        f"all related to material you've covered recently in "
        f"other cards—better to wait."
    )


@_auto_secondary_prompt
def _new_buried_over_daily_limit(review_availabilities, secondary=False):
    '''
    Buried new cards, past daily limit.

    Will never appear as the secondary prompt, since the "learn new cards"
    button does not appear when there are any cards due, nor when there are
    buried cards available under the daily limit.
    '''
    if secondary:
        return
    if not review_availabilities.new_cards_per_day_limit_reached:
        return
    count = review_availabilities.buried_new_cards_count
    if count == 0 or count is None:
        return
    already_learned = review_availabilities.new_cards_limit.learned_today_count
    cards_suffix = _manabi_reader_suffix(review_availabilities)
    return (
        f"We have {count} new {_pluralize_cards(count)}{cards_suffix} "
        f"only from material covered recently, "
        f"plus you've already learned {already_learned} today—better wait."
    )


@_auto_secondary_prompt
def _early_review(review_availabilities, **kwargs):
    '''
    Early review.
    '''
    if not review_availabilities.early_review_available:
        return
    if review_availabilities.next_new_cards_count > 0:
        if not review_availabilities.new_cards_per_day_limit_reached:
            return
        return (
            '''Good news is you're caught up on reviews! Consider taking a '''
            '''break or <a href="itms-apps://itunes.apple.com/app/id1247286380">reading</a> instead.'''
        )
    return '''You're caught up on reviews! Take a break or <a href="itms-apps://itunes.apple.com/app/id1247286380">go read something in Japanese</a>.'''


@_auto_secondary_prompt
def _done_early_review_of_all_cards(review_availabilities, secondary=False):
    '''
    When early review has finished and all cards have been reviewed at least
    once.
    '''
    if secondary:
        return
    if review_availabilities.early_review_began_at is None:
        return
    return (
        "You've reviewed every card at least once already now in this "
        '''session. Go take a break or <a href="itms-apps://itunes.apple.com/app/id1247286380">read something</a> instead.'''
    )


@_auto_secondary_prompt
def _all_cards_buffered(review_availabilities, secondary=False):
    '''
    When review has finished and all cards have been reviewed at least
    once (including excluded cards).
    '''
    if secondary:
        return
    if (
        review_availabilities.base_cards_queryset.exists()
        or not review_availabilities.excluded_card_ids
    ):
        return
    return (
        "You've reviewed every card at least once already now in this "
        '''session. Go take a break or <a href="itms-apps://itunes.apple.com/app/id1247286380">read something</a> instead.'''
    )


def review_availability_prompts(review_availabilities):
    # Be sure to synchronize with Card manager's `_next_card_funcs`.
    prompt_funcs = [
        _failed_due,
        _mature_due,
        # TODO:  _far_over_due,
        _young_due,
        _failed_not_due,
        _new_under_daily_limit,
        _new_over_daily_limit,
        _new_buried_under_daily_limit,
        _new_buried_over_daily_limit,
        _early_review,
        _done_early_review_of_all_cards,
        _all_cards_buffered,
    ]

    prompts = []

    for prompt_func in prompt_funcs:
        prompt = prompt_func(
            review_availabilities,
            secondary=(len(prompts) == 1))

        if prompt is not None:
            prompts.append(prompt)
        if len(prompts) == 2:
            break

    if len(prompts) == 0:
        return (None, None)
    elif len(prompts) == 1:
        return (prompts[0], None)

    return tuple(prompts)
