# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-01-02 07:56


from django.db import migrations


def forwards(apps, schema_editor):
    from autoslug.settings import slugify

    Deck = apps.get_model('flashcards', 'Deck')

    # Ported from Deck#delete
    for deck in Deck.objects.filter(active=False).iterator():
        deck.facts.update(active=False)
        deck.card_set.update(active=False)

        deck.subscriber_decks.clear()

        for fact in deck.facts.iterator():
            fact.subscriber_facts.clear()
        deck.facts.update(active=False)


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0034_deck_slugs_required'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]
