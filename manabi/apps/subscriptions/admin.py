from django.contrib import admin

from .models import (
    Subscription,
    InAppPurchaseLogItem,
    SubscriptionUpdateNotificationLogItem,
)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    fields = [
        'expires_date',
        'active',
        'is_trial_period',
    ]
    readonly_fields = [
        'subscriber',
        'created_at',
        'modified_at',
        'original_transaction_id',
    ]
    list_display = [
        'subscriber',
        'expires_date',
        'active',
        'is_trial_period',
        'original_transaction_id',
    ]


@admin.register(InAppPurchaseLogItem)
class InAppPurchaseLogItemAdmin(admin.ModelAdmin):
    pass


@admin.register(SubscriptionUpdateNotificationLogItem)
class SubscriptionUpdateNotificationLogItemAdmin(admin.ModelAdmin):
    pass
