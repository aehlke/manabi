# -*- coding: utf-8 -*-
# Generated by Django 1.11a1 on 2017-02-18 23:23


from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('flashcards', '0050_initialize_deck_suspended_denormalization'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='deck',
            unique_together=set([('owner', 'name', 'synchronized_with', 'active')]),
        ),
        migrations.AlterIndexTogether(
            name='card',
            index_together=set([('deck', 'owner'), ('owner', 'due_at', 'active', 'suspended')]),
        ),
    ]
