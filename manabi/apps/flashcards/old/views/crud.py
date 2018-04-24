# Although the API also has CRUD views, this module is just for 
# the regular HTML page views that pertain to CRUD, rather than the 
# JSON-formatted views that the API module handles.
#
# The CRUD aspect of this app is also the nastiest, but it works. I wrote it 
# before I knew what I was doing. It's the dullest part to rewrite though,
# so I won't get around to a significant rewrwite until later. It all works,
# after all.

from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db import transaction
from django.forms import forms
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext, loader
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from dojango.decorators import json_response
from dojango.util import to_dojo_data, json_decode, json_encode
from manabi.apps.flashcards.contextprocessors import subfact_form_context
from manabi.apps.flashcards.forms import DeckForm, FactForm, FieldContentForm
from manabi.apps.flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType
from manabi.apps.flashcards.models import FieldContent, Card
from manabi.apps.flashcards.forms import TextbookSourceForm
from manabi.apps.flashcards.views.shortcuts import get_deck_or_404
from manabi.apps.books.forms import TextbookForm
from manabi.apps import usertagging


def add_decks(request):
    '''Starting point for adding a deck, whether by creating or by downloading a shared deck.'''
    ctx = {}
    shared_decks = Deck.objects.shared_decks()
    if request.user.is_authenticated:
        shared_decks = shared_decks.exclude(owner=request.user)
        ctx['deck_list'] = Deck.objects.filter(owner=request.user, active=True).order_by('name')
    ctx['shared_deck_list'] = shared_decks
    return render_to_response('flashcards/add.html', ctx, context_instance=RequestContext(request))

def deck_detail(request, deck_id=None):
    deck = get_deck_or_404(request.user, deck_id)

    if request.user.is_authenticated:
        # Redirect if the user is already subscribed to this deck.
        subscriber = deck.get_subscriber_deck_for_user(request.user)
        if subscriber:
            return redirect(subscriber.get_absolute_url())

    fact_tags = deck.fact_tags()

    detail_args = {
        'queryset': Deck.objects.filter(active=True),
        'template_object_name': 'deck',
        'extra_context': {
            'field_types': FactType.objects.get(id=1).fieldtype_set.all().order_by('ordinal'),
            'fact_tags': fact_tags,

            'textbook_source_form': TextbookSourceForm(),
            'textbook_form': TextbookForm(),
        },
        'object_id': deck_id,

    }
    #detail_args['extra_context'].update(study_options_context(request, deck_id=deck_id))
    return DetailView.as_view(request, **detail_args)


@login_required
def facts_editor(request):
    #assume Japanese for now (model 1, the only model object)
    #get the fieldtypes for Japanese
    
    fact_type = FactType.objects.get(id=1)
    field_types = fact_type.fieldtype_set.all().order_by('ordinal')
    card_templates = fact_type.cardtemplate_set.all()
    decks = Deck.objects.filter(owner=request.user, active=True)
    context = {'field_types': field_types,
               'card_templates': card_templates,
               'decks': decks}
    return render_to_response('flashcards/facts_editor.html', context)


@login_required
def fact_update(request, fact_id):
    if request.method == 'GET':
        # if this is a subscribed fact that the subscriber hasn't copied yet, copy the fact (without its field contents) first
        fact = Fact.objects.get_for_owner_or_subscriber(fact_id, request.user)
        fact.edit_string_for_tags = usertagging.utils.edit_string_for_tags(fact.tags)
        fact_type = FactType.objects.get(id=1) #assume japanese for now
        decks = Deck.objects.filter(owner=request.user, active=True)
        card_templates = []
        activated_card_templates = [e.template for e
                                    in fact.card_set.filter(active=True)]

        for card_template in fact_type.cardtemplate_set.all():
            #TODO-OLD only send the id(uri)/name/status
            #card_templates.append({'card_template': card_template,
            #'activated_for_fact': (card_template in activated_card_templates)})
            card_template.activated_for_fact = (card_template
                                                in activated_card_templates)
            card_templates.append(card_template)

        context = {
            'fact': fact,
            'card_templates': card_templates,
            'decks': decks,
            'field_contents': fact.field_contents,
        }

        # subfact forms
        context.update(subfact_form_context(request))
        context['subfact_forms'] = []
        context['initial_field_content_form_count'] = fact.fieldcontent_set.count() + sum([subfact.fieldcontent_set.count() for subfact in fact.subfacts.all() if subfact.owner == request.user])
        i = 1
        field_content_offset = len(fact.field_contents)
        for subfact in fact.subfacts:
            context['subfact_forms'].append(subfact_form_context(request, subfact=subfact, field_content_offset=field_content_offset, fact_form_ordinal=i)['subfact_form'])
            i += 1
            field_content_offset += len(subfact.field_contents)
        return render_to_response('flashcards/fact_form.html', context, context_instance=RequestContext(request))


#CRUD forms
#TODO-OLD refactor into HTML/AJAX CRUD pattern
@login_required
def deck_list(request):
    decks = Deck.objects.filter(owner=request.user, active=True).order_by('name')
    context = {'container_id': 'deckDialog'}
    context['only_one_deck_exists'] = (len(decks) == 1)

    return ListView.as_view(request, queryset=decks, extra_context=context, template_object_name='deck')


@login_required
def deck_update(request, deck_id):
    deck = get_object_or_404(Deck, pk=deck_id)
    if deck.owner_id != request.user.id: #and not request.User.is_staff():
        raise forms.ValidationError('You do not have permission to access this flashcard deck.')
    if request.method == 'POST':
        deck_form = DeckForm(request.POST, instance=deck)
        if deck_form.is_valid():
            deck = deck_form.save()
            return HttpResponse(json_encode({'success':True}), mimetype='text/javascript')
    else:
        deck_form = DeckForm(instance=deck)
    return render_to_response('flashcards/deck_form.html', 
        {'form': deck_form,
         'deck': deck,
         'container_id': 'deckDialog',
         'post_save_redirect': '/flashcards/decks'}) #todo:post/pre redirs


@login_required
def deck_delete(request, deck_id, post_delete_redirect='/flashcards/decks'): #todo: pass post_*_redirect from urls.py
    obj = get_object_or_404(Deck, pk=deck_id)
    if obj.owner_id != request.user.id: #and not request.User.is_staff():
        raise forms.ValidationError('You do not have permission to access this flashcard deck.')
    if request.method == 'POST':
        if obj.subscriber_decks.filter(active=True).count() > 0: #exists():
            obj.active = False
            obj.save()
        else:
            obj.delete_cascading()
        return HttpResponse(json_encode({'success':True}), mimetype='text/javascript')
    else:
        return render_to_response('flashcards/deck_confirm_delete.html',
            {'deck': obj,
             'post_delete_redirect': post_delete_redirect,
             'container_id': 'deckDialog'})

@login_required
def deck_create(request,
                post_save_redirect=None,
                cancel_redirect='add_decks'):
    cancel_redirect = reverse(cancel_redirect)

    if post_save_redirect is not None:
        post_save_redirect = reverse(post_save_redirect)

    if request.method == 'POST':

        deck_form = DeckForm(request.POST)
        if deck_form.is_valid():
            new_deck = deck_form.save(commit=False)
            new_deck.owner = request.user
            new_deck.save()

            if 'tags' in deck_form.cleaned_data:
                    new_deck.tags = deck_form.cleaned_data['tags']

            if post_save_redirect is None:
                post_save_redirect = new_deck.get_absolute_url()
            else:
                post_save_redirect = reverse(post_save_redirect)

            return HttpResponse(json_encode({'success': True, 'postRedirect': post_save_redirect}), mimetype='text/javascript')
        else:
            #FIXME post_redirect for failure? handle in ajax?
            return HttpResponse(json_encode({'success': False}), mimetype='text/javascript')
    else:
            deck_form = DeckForm()
    return render_to_response('flashcards/deck_form.html', 
        {'form': deck_form,
         'post_save_redirect': post_save_redirect,
         'cancel_redirect': cancel_redirect,
        } , context_instance=RequestContext(request)) #todo:post/pre redirs





@login_required
def deck_export_to_csv(request, deck_id):
    '''
    Terrible CSV generator.

    sample:
        Expression,Reading,Meaning,Production,Recognition
        TAberu,TA[ta]beru,to eat,off,on
    '''
    deck = get_object_or_404(Deck, pk=deck_id)

    if deck.owner_id != request.user.id: #and not request.User.is_staff():
        raise forms.ValidationError('You do not have permission to access this flashcard deck.')
    
    return deck.export_to_csv()






