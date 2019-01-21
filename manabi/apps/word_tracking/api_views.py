from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import TrackedWordsSerializer
from .models import TrackedWords


class TrackedWordsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, format=None):
        tracked_words = TrackedWords(request.user)
        serializer = TrackedWordsSerializer(tracked_words)
        return Response(serializer.data)
