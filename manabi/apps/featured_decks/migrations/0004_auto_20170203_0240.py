# -*- coding: utf-8 -*-
# Generated by Django 1.11a1 on 2017-02-03 02:40


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0042_auto_20170131_0014'),
        ('featured_decks', '0003_auto_20170201_0021'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='featureddeck',
            name='item_content_type',
        ),
        migrations.RemoveField(
            model_name='featureddeck',
            name='item_id',
        ),
        migrations.AddField(
            model_name='featureddeck',
            name='deck_collection',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='flashcards.DeckCollection'),
        ),
    ]
