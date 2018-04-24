from django.shortcuts import render

from manabi.apps.flashcards.models import Deck


def homepage(request):
    if request.user.is_anonymous:
        return render(request, 'landing_page.html')

    decks = Deck.objects.of_user(request.user)

    return render(request, 'homepage.html', {
        'decks': decks,
    })
