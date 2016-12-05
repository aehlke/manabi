# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from rest_framework import status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from manabi.api.renderers import ModelViewSetHTMLRenderer
from manabi.apps.flashcards import api_views
from manabi.apps.flashcards.models import (
    Deck,
)
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

    def get_queryset(self):
        '''
        Includes subscriber decks in order to allow redirecting upstream.
        '''
        if self.action == 'list':
            return super(DeckViewSet, self).get_queryset()

        filters = (
            Q(active=True, shared=True)
            | Q(synchronized_with__isnull=False)
        )

        if self.request.user.is_authenticated():
            filters |= Q(active=True, owner=self.request.user)

        return Deck.objects.filter(filters).order_by('name')

    def _redirect_to_upstream_deck_if_anonymous(self, url_name):
        deck = self.get_object()
        if (
                self.request.user.is_anonymous()
                and deck.synchronized_with is not None
        ):
            upstream_deck = deck.synchronized_with
            return redirect(url_name,
                            pk=upstream_deck.pk, slug=upstream_deck.slug)

    def _redirect_to_owner_deck_if_subscriber(self, url_name):
        if self.request.user.is_anonymous():
            return

        deck = self.get_object()
        subscriber_deck_for_viewer = deck.get_subscriber_deck_for_user(
            self.request.user)

        if subscriber_deck_for_viewer is None:
            return

        return redirect(url_name,
                        pk=subscriber_deck_for_viewer.pk,
                        slug=subscriber_deck_for_viewer.slug)

    def list(self, request):
        if self.request.user.is_anonymous():
            return redirect('shared-deck-list')

        response = super(DeckViewSet, self).list(request)
        response.template_name = 'flashcards/deck_list.html'
        return response

    def retrieve(self, request, pk=None, slug=None):
        deck = self.get_object()
        if slug != deck.slug:
            return redirect('deck-detail', pk=deck.pk, slug=deck.slug)

        response = (
            self._redirect_to_upstream_deck_if_anonymous('deck-detail')
            or self._redirect_to_owner_deck_if_subscriber('deck-detail'))
        if response:
            return response

        response = super(DeckViewSet, self).retrieve(request, pk=pk)
        response.template_name = 'flashcards/deck_detail.html'
        return response

    @detail_route()
    def facts(self, request, pk=None, slug=None):
        deck = self.get_object()
        if slug != deck.slug:
            return redirect('deck-facts', pk=deck.pk, slug=deck.slug)

        response = (
            self._redirect_to_upstream_deck_if_anonymous('deck-facts')
            or self._redirect_to_owner_deck_if_subscriber('deck-facts'))
        if response:
            return response

        return Response(
            DetailedDeckSerializer(deck).data,
            template_name='flashcards/deck_facts.html',
        )


class SharedDeckViewSet(api_views.SharedDeckViewSet):
    renderer_classes = [ModelViewSetHTMLRenderer]

    def list(self, request):
        response = super(SharedDeckViewSet, self).list(request)
        response.template_name = 'flashcards/shared_deck_list.html'
        return response
