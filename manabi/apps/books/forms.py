from django import forms
from .models import Textbook
from manabi.apps.flashcards.models import Deck

class TextbookForm(forms.ModelForm):
    '''
    Used for setting the textbook source of a deck.
    '''
    class Meta:
        model = Textbook
        fields = ('isbn',)

