from rest_framework import serializers


class TrackedWordsSerializer(serializers.Serializer):
    learning_jmdict_ids = serializers.ListField(
        child=serializers.IntegerField())
    known_jmdict_ids = serializers.ListField(
        child=serializers.IntegerField())

    learning_words_without_jmdict_ids = serializers.ListField(
        child=serializers.CharField())
    known_words_without_jmdict_ids = serializers.ListField(
        child=serializers.CharField())
