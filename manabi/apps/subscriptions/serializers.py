from rest_framework import serializers


class SubscriptionProduct(serializers.Serializer):
    product_id = serializers.CharField()
    subtitle = serializers.CharField()


class PurchasedSubscriptionProductSerializer(serializers.Serializer):
    itunes_receipt = serializers.CharField()
    subscription_is_active = serializers.BooleanField(read_only=True)


class PurchasingOptionsSerializer(serializers.Serializer):
    primary_prompt = serializers.CharField()
    student_prompt = serializers.CharField()
    monthly_product = SubscriptionProduct()
    annual_product = SubscriptionProduct()
    student_monthly_product = SubscriptionProduct()
    student_annual_product = SubscriptionProduct()


class SubscriptionStatusSerializer(serializers.Serializer):
    active = serializers.BooleanField(read_only=True)
