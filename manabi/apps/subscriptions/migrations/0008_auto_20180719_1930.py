# Generated by Django 2.0.4 on 2018-07-19 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0007_subscription_is_trial_period'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='inapppurchaselogitem',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='subscription',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='subscriptionupdatenotificationlogitem',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='inapppurchaselogitem',
            name='original_transaction_id',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name='subscriptionupdatenotificationlogitem',
            name='original_transaction_id',
            field=models.CharField(blank=True, max_length=300),
        ),
    ]