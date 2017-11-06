from rest_framework import serializers

class ReviewResultsSerializer(serializers.Serializer):
    cards_reviewed = serializers.IntegerField()
    current_daily_streak = serializers.IntegerField()
    was_review_first_of_today = serializers.BooleanField()
    days_reviewed_by_week = serializers.JSONField()
