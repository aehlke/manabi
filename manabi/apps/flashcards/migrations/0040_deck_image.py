# -*- coding: utf-8 -*-
# Generated by Django 1.11a1 on 2017-01-24 00:41


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0039_auto_20170123_0352'),
    ]

    operations = [
        migrations.AddField(
            model_name='deck',
            name='image',
            field=models.ImageField(blank=True, upload_to=b''),
        ),
    ]
