# Generated by Django 2.1.5 on 2019-01-20 23:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0061_auto_20190120_2302'),
    ]

    operations = [
        migrations.RenameField(
            model_name='card',
            old_name='modified_at',
            new_name='created_or_modified_at',
        ),
    ]
