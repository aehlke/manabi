# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-03-04 21:37
from __future__ import unicode_literals

from django.db import migrations


def forwards(apps, schema_editor):
    from manabi.apps.twitter_usages.harvest import tweet_is_spammy

    ExpressionTweet = apps.get_model('twitter_usages', 'ExpressionTweet')

    for expression_tweet in ExpressionTweet.objects.all().iterator():
        if tweet_is_spammy(expression_tweet.tweet):
            print 'Deleting spammy tweet', expression_tweet.tweet['text'].encode('ascii')
            expression_tweet.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('twitter_usages', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards),
    ]
