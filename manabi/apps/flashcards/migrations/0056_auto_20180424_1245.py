# Generated by Django 2.0.4 on 2018-04-24 12:45

import autoslug.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0055_refresh_card_counts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='template',
            field=models.SmallIntegerField(choices=[(0, 'Production'), (1, 'Recognition'), (2, 'Kanji Reading'), (3, 'Kanji Writing')]),
        ),
        migrations.AlterField(
            model_name='deck',
            name='image',
            field=models.ImageField(blank=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='deck',
            name='slug',
            field=autoslug.fields.AutoSlugField(always_update=True, editable=False, populate_from='name'),
        ),
        migrations.AlterField(
            model_name='deckcollection',
            name='image',
            field=models.ImageField(blank=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='deckcollection',
            name='slug',
            field=autoslug.fields.AutoSlugField(always_update=True, editable=False, populate_from='name'),
        ),
        migrations.AlterField(
            model_name='textbook',
            name='custom_title',
            field=models.CharField(blank=True, help_text='Set this to override the Amazon product name.', max_length=200),
        ),
    ]