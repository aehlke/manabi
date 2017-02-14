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
            if parts[0].lower() in ["we", "we'll", "you", "you'll"]:
                prompt = u' '.join(parts[:1] + ['also'] + parts[1:])
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

@_auto_secondary_prompt
def _failed_due(review_availabilities, secondary=False):
    '''
    Failed, due.
    '''
    cards = review_availabilities.base_cards_queryset
    count = cards.failed().due().count()
    if count == 0:
        return
    return (
        u"You're ready to revisit {} {} that you had forgotten."
    ).format(count, _pluralize_cards(count), _pluralize('is', 'are', count))


@_auto_secondary_prompt
def _mature_due(review_availabilities, secondary=False):
    '''
    Mature, due.
    '''
    cards = review_availabilities.base_cards_queryset
    count = cards.mature().due().excluding_failed().count()
    if count == 0:
        return
    return (
        u"We have {} {} that you know well but may forget if left unused much longer."
    ).format(count, _pluralize_cards(count))


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
    return (
        u"You'll soon forget {} {} you're still learning—now's an effective "
        u"time to reinforce {}."
    ).format(count, _pluralize_cards(count), _pluralize('it', 'them', count))


@_auto_secondary_prompt
def _failed_not_due(review_availabilities, secondary=False):
    '''
    Failed, not due.
    '''
    cards = review_availabilities.base_cards_queryset
    count = cards.failed().due().count()
    if count == 0:
        return
    return (
        u"We have {} {} you had forgotten last time that {} ready to be revisited."
    ).format(count, _pluralize_cards(count), _pluralize('is', 'are', count))


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

    if review_availabilities.new_cards_limit.learned_today_count > 0:
        template = u"We have {} more new {} for you to learn."
    else:
        template = u"We have {} new {} for you to learn."
    return template.format(count, _pluralize_cards(count))


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
    return (
        u"You've already learned {already_learned} new {cards} today, but we have {next_new_count} more if you're feeling ambitious."
    ).format(
        next_new_count=count,
        already_learned=(
            review_availabilities.new_cards_limit.learned_today_count),
        cards=_pluralize_cards(count),
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

    template = (
        u"We have {} new {}, all related to material you've "
        u"covered recently in other cards—better to wait."
    )
    return template.format(count, _pluralize_cards(count))


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

    template = (
        u"We have {} new {} only from material covered recently, "
        u"plus you've already learned {} today—better wait."
    )
    return template.format(
        count, _pluralize_cards(count),
        review_availabilities.new_cards_limit.learned_today_count)


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
            u"Good news is you're caught up on reviews! Consider taking a "
            u"break or reading instead."
        )
    return u"You're caught up on reviews! Take a break or go read something."


@_auto_secondary_prompt
def _done_early_review_of_all_cards(review_availabilities, secondary=False):
    '''
    When early review has finished and all cards have been reviewed at least
    once.
    '''
    if secondary:
        return
    # TODO: Verify the user is in early_review mode.
    return (
        u"You've reviewed every card at least once already now in this "
        u"session. Go take a break or read something instead."
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
    ]

    prompts = []

    for prompt_func in prompt_funcs:
        prompt = prompt_func(review_availabilities, secondary=(len(prompts) == 1))
        if prompt is not None:
            prompts.append(prompt)
        if len(prompts) == 2:
            break

    if len(prompts) == 0:
        return (None, None)
    elif len(prompts) == 1:
        return (prompts[0], None)

    return tuple(prompts)
