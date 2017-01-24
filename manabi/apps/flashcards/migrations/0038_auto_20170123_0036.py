# -*- coding: utf-8 -*-
# Generated by Django 1.11a1 on 2017-01-23 00:36
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0037_initialize_card_owner_denormalization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='owner',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]