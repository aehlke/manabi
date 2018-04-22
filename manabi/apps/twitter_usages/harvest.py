# -*- coding: utf-8 -*-
import itertools

from django.db import IntegrityError
from django.db.models import Q
from django.conf import settings
from natto import MeCab
from twython import Twython

from manabi.apps.twitter_usages.models import (
    ExpressionTweet,
    search_expressions,
)


def _search_tweets(term, count):
    twitter = Twython(settings.TWITTER_APP_KEY, settings.TWITTER_APP_SECRET)
    return twitter.search(
        q=u'"{}"'.format(term),
        lang='ja',
        result_type='mixed',
        count=count,
    )['statuses']


def tweet_is_spammy(tweet):
    display_name = tweet['user']['name'].lower()

    if tweet['text'].strip()[:1] == u'【':
        return True

    if tweet['text'].strip().startswith(u'定期自己紹介'):
        return True

    for ad_word in [
        u'[定期]', u'(定期)', u'【定期】', u'《定期》', u'定期：',
        u'※定期※ ', u'〈定期〉', u'↓続く', u'【迷言定期】',
        u'☆定期☆', u'『定期』',
    ]:
        if ad_word in tweet['text'] or ad_word in display_name:
            return True

    if tweet['user']['screen_name'].lower().endswith('_bot'):
        return True

    if (
        '(bot)' in display_name
        or u'（BOT）' in display_name
        or display_name.endswith('bot')
        or display_name.endswith(u'ボット')
    ):
        return True

    return False


def cull_spammy_tweets(tweets, desired_count):
    good_tweets = []
    tweet_texts = set()

    for tweet in tweets:
        if tweet_is_spammy(tweet):
            continue

        if tweet['text'] in tweet_texts:
            continue

        good_tweets.append(tweet)
        tweet_texts.add(tweet['text'])

        if len(good_tweets) == desired_count:
            break

    return good_tweets


def sorted_by_usefulness_estimate(tweets_with_frequencies):
    def sort_key(item):
        frequency, tweet = item

        maybe_spam = (
            '|' in tweet['text'] 
            or u'①' in tweet['text']
            or 'RT:' in tweet['text']
            or '#RT' in tweet['text']
        )

        return (0 if maybe_spam else 1, -frequency)

    return sorted(
        tweets_with_frequencies,
        key=sort_key)


def word_frequencies(text):
    from manabi.apps.reading_level.word_frequencies import WORD_FREQUENCIES

    mecab = MeCab()
    frequencies = []
    for node in mecab.parse(text.encode('utf8'), as_nodes=True):
        frequency = WORD_FREQUENCIES.get(node.surface.decode('utf8'))
        if frequency is None:
            continue
        frequencies.append(frequency)
    return frequencies


def harvest_tweets(fact, tweets_per_fact=10):
    if settings.TWITTER_APP_KEY is None:
        return

    if not fact.expression:
        return

    for expression in search_expressions(fact):
        SEARCH_COUNT = 100
        tweets = _search_tweets(expression, SEARCH_COUNT)
        tweets = cull_spammy_tweets(tweets, SEARCH_COUNT)

        tweets_with_frequencies = []
        for tweet in tweets:
            frequencies = word_frequencies(tweet['text'])
            try:
                average = sum(frequencies) / float(len(frequencies))
            except ZeroDivisionError:
                average = 0
            tweets_with_frequencies.append((average, tweet))

        sorted_tweets = sorted_by_usefulness_estimate(
            tweets_with_frequencies)

        top_tweets = sorted_tweets[:tweets_per_fact]

        for average_word_frequency, tweet in top_tweets:
            try:
                ExpressionTweet.objects.create(
                    search_expression=expression,
                    tweet=tweet,
                    tweet_id=tweet['id_str'],
                    average_word_frequency=average_word_frequency,
                )
            except IntegrityError:
                continue


def harvest_tweets_for_facts(fact_count):
    from manabi.apps.flashcards.models import Fact

    facts = Fact.objects.exclude(expression='').order_by('?')
    facts = facts.exclude(Q(forked=False) & Q(synchronized_with_id__isnull=False))

    # TODO This is probably temporary for initial migration.
    # facts = facts.filter(deck__owner__username='alex')
    facts = facts.exclude(
        expression__in=
        ExpressionTweet.objects.values_list('search_expression').distinct(),
    )
    print('Remaining facts: {}'.format(facts.count()))

    facts = facts[:fact_count]

    for fact in facts.iterator():
        print('Fact {}:'.format(fact.id), fact.expression)

        harvest_tweets(fact)
