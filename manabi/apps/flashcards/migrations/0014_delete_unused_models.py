# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-26 02:45


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0013_auto_20160826_0243'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CardTemplate',
        ),
        migrations.DeleteModel(
            name='FactType',
        ),
        migrations.DeleteModel(
            name='FieldContent',
        ),
    ]
