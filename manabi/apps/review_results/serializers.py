from rest_framework import serializers

class ReviewResultsSerializer(serializers.Serializer):
    cards_reviewed = serializers.IntegerField()
    current_daily_streak = serializers.IntegerField()
    days_reviewed_by_week = serializers.JSONField()
