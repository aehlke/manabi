from datetime import datetime

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_condition import last_modified

from .serializers import TrackedWordsSerializer
from .models import TrackedWords


def tracked_words_last_modified(request):
    tracked_words = TrackedWords(request.user)
    return tracked_words.last_modified


class TrackedWordsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @last_modified(tracked_words_last_modified)
    def list(self, request, format=None):
        tracked_words = TrackedWords(request.user)
        serializer = TrackedWordsSerializer(tracked_words)
        return Response(serializer.data)
