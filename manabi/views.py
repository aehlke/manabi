from django.shortcuts import render


def homepage(request):
    if request.user.is_anonymous():
        return render(request, 'landing_page.html')
