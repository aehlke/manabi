from functools import wraps


def _auto_secondary_prompt(f):
    @wraps(f)
    def wrapper(*args, secondary=False, **kwargs):
        prompt = f(*args, secondary=secondary, **kwargs)
        if secondary:
            parts = prompt.split(' ')
            prompt = parts[:1] + ['also'] + parts[1:]
        return prompt
    return wrapper


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
        u"We have {} cards you had forgotten last time that are ready to be revisited."
    ).format(count)


@_auto_secondary_prompt
def _mature_due(review_availabilities, secondary=False):
    '''
    Mature, due.
    '''
    cards = review_availabilities.base_cards_queryset
    count = cards.mature().due().count()
    if count == 0:
        return
    return (
        u"We have {} cards that you know well but may forget soon if left unused."
    ).format(count)


# TODO
# def _far_over_due(review_availabilities, secondary=False):
#     '''
#     Far over-due.
#     '''
#     return u"You may have already forgotten {} cards—pick them up again quickly through review."


@_auto_secondary_prompt
def _young_due(review_availabilities, secondary=False):
    '''
    Young, due.
    '''
    cards = review_availabilities.base_cards_queryset
    count = cards.young().due().count()
    if count == 0:
        return
    return (
        u"You'll soon forget {} cards that you're still learning—now's the most effective time to reinforce them."
    ).format(count)


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
    return (
        u"We have {} new cards for you to learn."
    ).format(count)


@_auto_secondary_prompt
def _new_over_daily_limit(review_availabilities, secondary=False):
    '''
    Next new cards, past daily limit.
    '''
    if not review_availabilities.new_cards_per_day_limit_reached:
        return
    count = review_availabilities.next_new_cards_count
    if count == 0:
        return
    return (
        u"You've already learned {} new cards today, but we have more if you're feeling ambitious."
    ).format(count)


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
            u"break or go read something instead."
        )
    return u"You're caught up on reviews! Take a break or go read something."


def review_availability_prompts(review_availabilities):
    # Be sure to synchronize with Card manager's `_next_card_funcs`.
    prompt_funcs = [
        _failed_due,
        _mature_due,
        # TODO:  _far_over_due,
        _failed_not_due,
        _young_due,
        _new_under_daily_limit,
        _new_over_daily_limit,
        _early_review,
    ]

    prompts = []

    for prompt_func in prompt_funcs:
        prompt = prompt_func(review_availabilities, secondary=(len(prompts) == 1))
        if prompt is not None:
            prompts.append(prompt)
        if len(prompts) == 2:
            break

    return tuple(*prompts)
