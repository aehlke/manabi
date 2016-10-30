from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def card_creator(request):
    return render(request, 'homepage.html')
