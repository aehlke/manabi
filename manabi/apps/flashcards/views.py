from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.decorators import list_route
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from manabi.apps.flashcards import api_views
from manabi.apps.flashcards.serializers import (
    FactWithCardsSerializer,
)


class FactViewSet(api_views.FactViewSet):
    @list_route(renderer_classes=[TemplateHTMLRenderer])
    def creator(self, request, *args, **kwargs):
        serializer = FactWithCardsSerializer(
            context={'user': request.user},
        )

        return Response(
            {
                'serializer': serializer,
            },
            template_name='flashcards/facts_creator.html',
        )
