from rest_framework import serializers

class ReviewResultsSerializer(serializers.Serializer):
    cards_reviewed = serializers.IntegerField()
