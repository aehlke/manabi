# Generated by Django 2.0.4 on 2018-07-12 01:40

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subscriptions', '0003_subscription_expires_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='InAppPurchaseLogItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('itunes_receipt', models.TextField(editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('subscriber', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SubscriptionUpdateNotificationLogItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receipt_info', django.contrib.postgres.fields.jsonb.JSONField(editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
