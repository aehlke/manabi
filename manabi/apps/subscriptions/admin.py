from django.contrib import admin

from .models import (
    Subscription,
    InAppPurchaseLogItem,
    SubscriptionUpdateNotificationLogItem,
)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    pass


@admin.register(InAppPurchaseLogItem)
class InAppPurchaseLogItemAdmin(admin.ModelAdmin):
    pass


@admin.register(SubscriptionUpdateNotificationLogItem)
class SubscriptionUpdateNotificationLogItemAdmin(admin.ModelAdmin):
    pass
