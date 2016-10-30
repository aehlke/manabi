from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from manabi.apps.flashcards import api_views


class FactViewSet(api_views.FactViewSet):
    renderer_classes = [ManabiHTMLRenderer, JSONRenderer]
    template_name = 'flashcards/facts.html'
