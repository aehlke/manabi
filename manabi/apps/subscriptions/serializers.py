from rest_framework import serializers


class SubscriptionProduct(serializers.Serializer):
    product_id = serializers.CharField()
    subtitle = serializers.CharField()


class PurchasedSubscriptionProduct(serializers.Serializer):
    itunes_receipt = serializers.CharField()


class PurchasingOptionsSerializer(serializers.Serializer):
    primary_prompt = serializers.CharField()
    student_prompt = serializers.CharField()
    monthly_product = SubscriptionProduct()
    annual_product = SubscriptionProduct()
    student_monthly_product = SubscriptionProduct()
    student_annual_product = SubscriptionProduct()
