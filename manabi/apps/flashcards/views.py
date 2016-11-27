# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from rest_framework.decorators import detail_route, list_route
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from manabi.api.renderers import ModelViewSetHTMLRenderer
from manabi.apps.flashcards import api_views
from manabi.apps.flashcards.serializers import (
    FactWithCardsSerializer,
    DetailedDeckSerializer,
    DetailedSharedDeckSerializer,
)


class FactViewSet(api_views.FactViewSet):
    serializer_class = FactWithCardsSerializer
    serializer_action_classes = {}

    renderer_classes = [TemplateHTMLRenderer]

    @list_route(
        methods=['GET', 'POST'],
        renderer_classes=[TemplateHTMLRenderer],
    )
    def creator(self, request, *args, **kwargs):
        if request.method == 'GET':
            return Response({
                'serializer': self.get_serializer(),
            }, template_name='flashcards/fact_creator.html')

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'serializer': serializer,
            }, template_name='flashcards/fact_creator.html')
        fact = serializer.save()

        messages.success(
            request._request,
            mark_safe((
                u'''Created flashcards for <a href="{}" class="alert-link">'''
                u'''「{}」</a>.'''
            ).format(
                reverse('fact-detail', args=[fact.id]),
                escape(fact.expression),
            ))
        )

        return redirect('homepage')


    def retrieve(self, request, pk=None):
        fact = self.get_object()
        serializer = self.get_serializer(fact)

        return Response({
            'serializer': serializer,
            'fact': fact,
        }, template_name='flashcards/fact.html')

    def post(self, request, pk=None):
        fact = self.get_object()
        serializer = self.get_serializer(fact, data=request.data)
        if not serializer.is_valid():
            return Response({
                'serializer': serializer,
                'fact': fact,
            }, template_name='flashcards/fact.html')
        serializer.save()
        return Response({
            'serializer': serializer,
            'fact': fact,
        }, template_name='flashcards/fact.html')


class DeckViewSet(api_views.DeckViewSet):
    renderer_classes = [ModelViewSetHTMLRenderer]

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
