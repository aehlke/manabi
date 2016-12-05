from django.shortcuts import get_object_or_404, render
from django.contrib.auth import get_user_model

from manabi.apps.flashcards.models import Deck


def user_profile(request, username):
    user = get_object_or_404(get_user_model(), username=username)

    decks = Deck.objects.of_user(user)
    if request.user.is_anonymous() or request.user.pk != user.pk:
        decks = decks.filter(shared=True)

    return render(request, 'profiles/user_profile.html', {
        'profile_user': user,
        'decks': Deck.objects.of_user(user),
    })
