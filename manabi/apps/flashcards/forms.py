from django import forms

from .models import Card, CardHistory, Fact, Deck

#Forms
#todo:row-level authentication (subclassing formset)



class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        exclude = ('fact', 'ease_factor', )


class DeckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = ('name', 'description')


class TextbookSourceForm(forms.ModelForm):
    '''
    Used for setting the textbook source of a deck.
    '''
    class Meta:
        model = Deck
        fields = ('textbook_source',)
