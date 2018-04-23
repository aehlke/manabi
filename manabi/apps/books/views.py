from django.contrib.auth.decorators import login_required
from django.contrib.humanize.templatetags.humanize import naturalday
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext, loader
from django.views.decorators.http import require_POST
from dojango.decorators import json_response
from dojango.util import to_dojo_data, json_decode, json_encode

from manabi.apps.flashcards.forms import TextbookSourceForm
from manabi.apps.flashcards.views.shortcuts import get_deck_or_404
from .forms import TextbookForm
from .models import Textbook


def book_list(request):
    context = {
        'books': Textbook.decked_objects.all()
    }
    return render_to_response('books/book_list.html', context,
        context_instance=RequestContext(request))

def book_detail(request, object_id=None, slug=None):
    book = get_object_or_404(Textbook, pk=object_id)

    # If the slug is wrong, redirect to the proper URL.
    if book.get_absolute_url() != request.path:
        return redirect(book, permanent=True)

    context = {
        'book': book,
    }
    return render_to_response('books/book_detail.html', context,
            context_instance=RequestContext(request))


@login_required
@require_POST
def deck_textbook_source(request, deck_id=None):
    '''
    Expects 2 forms, at least one filled.
    Reusing a textbook takes precedence over creating a new one.
    '''
    deck = get_deck_or_404(request.user, deck_id, must_own=True)

    old_form = TextbookSourceForm(request.POST, instance=deck)
    new_form = TextbookForm(request.POST)

    success = True
    will_create_new_book = True

    if old_form.is_valid():
        deck = old_form.save()
        will_create_new_book = deck.textbook_source is None
    else:
        success = False
    if new_form.is_valid() and will_create_new_book:
        textbook = new_form.save()
        deck.textbook_source = textbook
        deck.save()
    elif not new_form.is_valid():
        success = False

    return HttpResponse(json_encode({'success': success}), mimetype='text/javascript')




