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
    readonly_fields = [
        'subscriber',
        'created_at',
        'itunes_receipt',
        'original_transaction_id',
    ]
    list_display = [
        'subscriber',
        'original_transaction_id',
        'created_at',
    ]


@admin.register(SubscriptionUpdateNotificationLogItem)
class SubscriptionUpdateNotificationLogItemAdmin(admin.ModelAdmin):
    readonly_fields = [
        'receipt_info',
        'original_transaction_id',
        'created_at',
    ]
    list_display = [
        'original_transaction_id',
        'created_at',
    ]
