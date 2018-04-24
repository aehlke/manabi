from django.shortcuts import get_object_or_404
from rest_framework import permissions

from manabi.apps.flashcards.models import Deck


WRITE_ACTIONS = ['create', 'update', 'partial_update', 'delete']


class DeckSynchronizationPermission(permissions.BasePermission):
    message = "You don't have permission to add this deck to your library."

    def has_permission(self, request, view):
        if view.action in WRITE_ACTIONS:
            upstream_deck = get_object_or_404(
                Deck, pk=request.data['synchronized_with'])
            return upstream_deck.shared
        return True


class IsOwnerPermission(permissions.BasePermission):
    message = "You don't own this."

    def has_object_permission(self, request, view, obj):
        if view.action in WRITE_ACTIONS:
            return (
                request.user.is_authenticated and
                obj.owner.pk == request.user.pk
            )
        return True
