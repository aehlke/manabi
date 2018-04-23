# -*- coding: utf-8 -*-
from django.contrib.postgres.fields import JSONField
from django.db import models


class ExpressionTweet(models.Model):
    search_expression = models.CharField(max_length=500)
    #canonical_reading = models.CharField(max_length=1500, blank=True)
    tweet = JSONField()
    tweet_id = models.CharField(unique=True, max_length=20)
    average_word_frequency = models.FloatField()


def search_expressions(fact):
    '''
    Returns list of strings that should be used to search for usages for the
    given fact.
    '''
    suru = '（する）'
    if suru in fact.expression:
        return [
            fact.expression.replace(suru, ''),
            fact.expression.replace(suru, 'する'),
        ]

    return [fact.expression]
