# -*- coding: utf-8 -*-
# Generated by Django 1.11a1 on 2017-02-04 19:55
from __future__ import unicode_literals

from django.db import migrations


def forwards(apps, schema_editor):
    Deck = apps.get_model('flashcards', 'Deck')

    for deck in Deck.objects.filter(synchronized_with__isnull=False).iterator():
        deck.collection = deck.synchronized_with.collection
        deck.image = deck.synchronized_with.image
        deck.save(update_fields=['collection', 'image'])


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0042_auto_20170131_0014'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]