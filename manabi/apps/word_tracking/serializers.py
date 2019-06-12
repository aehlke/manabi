from rest_framework import serializers


class TrackedWordsSerializer(serializers.Serializer):
    suspended_jmdict_ids = serializers.ListField(
        child=serializers.IntegerField())
    new_jmdict_ids = serializers.ListField(
        child=serializers.IntegerField())
    learning_jmdict_ids = serializers.ListField(
        child=serializers.IntegerField())
    known_jmdict_ids = serializers.ListField(
        child=serializers.IntegerField())

    suspended_words_without_jmdict_ids = serializers.ListField(
        child=serializers.CharField())
    new_words_without_jmdict_ids = serializers.ListField(
        child=serializers.CharField())
    learning_words_without_jmdict_ids = serializers.ListField(
        child=serializers.CharField())
    known_words_without_jmdict_ids = serializers.ListField(
        child=serializers.CharField())
