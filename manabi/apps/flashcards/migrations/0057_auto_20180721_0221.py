# Generated by Django 2.0.4 on 2018-07-21 02:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0056_auto_20180424_1245'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='fact',
            unique_together={('deck', 'expression', 'reading', 'meaning'), ('deck', 'synchronized_with')},
        ),
    ]
