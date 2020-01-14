# Generated by Django 2.2.5 on 2019-11-03 15:48

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('flashcards', '0063_add_fact_suspended_denormalized_field'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='card',
            index_together={('owner', 'due_at', 'active', 'suspended', 'due_at', 'fact', 'deck_suspended'), ('owner', 'due_at', 'active', 'suspended'), ('deck', 'owner')},
        ),
        migrations.RemoveField(
            model_name='card',
            name='fact_suspended',
        ),
    ]