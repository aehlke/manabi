from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.decorators import detail_route, list_route
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from manabi.apps.flashcards import api_views
from manabi.apps.flashcards.serializers import (
    FactWithCardsSerializer,
    DetailedDeckSerializer,
    DetailedSharedDeckSerializer,
)


class FactViewSet(api_views.FactViewSet):
    @list_route(renderer_classes=[TemplateHTMLRenderer])
    def creator(self, request, *args, **kwargs):
        serializer = FactWithCardsSerializer(
            context={'user': request.user},
        )

        return Response(
            {'serializer': serializer},
            template_name='flashcards/fact_creator.html',
        )


class DeckViewSet(api_views.DeckViewSet):
    render_classes = [TemplateHTMLRenderer]

    def list(self, request):
        response = super(DeckViewSet, self).list(request)
        response.template_name = 'flashcards/deck_list.html'
        return response

    def retrieve(self, request, pk=None):
        response = super(DeckViewSet, self).retrieve(request, pk=pk)
        response.template_name = 'flashcards/deck_detail.html'
        return response

    @detail_route()
    def facts(self, request, pk=None):
        deck = self.get_object()
        return Response(
            DetailedDeckSerializer(deck).data,
            template_name='flashcards/deck_facts.html',
        )
