# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-14 01:29


import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_auto_20180113_0111'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='expires_date',
            field=models.DateTimeField(default=datetime.datetime(2018, 1, 14, 1, 29, 35, 921814)),
            preserve_default=False,
        ),
    ]
