from account.forms import SignupForm as PinaxSignupForm, OpenIDSignupForm as PinaxOpenIDSignupForm
from timezones.forms import TimeZoneField
from django.utils.translation import ugettext_lazy as _, ugettext
from django import forms

ios_attrs = {
    'autocapitalize': 'off',
    'autocorrect': 'off'
}

class SignupForm(PinaxSignupForm):
    username = forms.CharField(
        label = _("Username"),
        max_length = 30,
        widget = forms.TextInput(attrs=ios_attrs)
    )
    password1 = forms.CharField(
        label = _("Password"),
        widget = forms.PasswordInput(render_value=False, attrs=ios_attrs)
    )
    password2 = forms.CharField(
        label = _("Password (again)"),
        widget = forms.PasswordInput(render_value=False, attrs=ios_attrs)
    )
    email = forms.EmailField(widget=forms.TextInput(attrs=ios_attrs))
    timezone = TimeZoneField(label=_("Timezone"), required=True, initial='America/New_York')

#class OpenIDSignupForm(PinaxOpenIDSignupForm):
#    timezone = TimeZoneField(label=_("Timezone"), required=True, initial='America/New_York')
#    email = forms.EmailField(widget=forms.TextInput(), required=True)

#    def __init__(self, *args, **kwargs):
#        # remember provided (validated!) OpenID to attach it to the new user
#        # later.
#        self.openid = kwargs.pop("openid", None)
#        # pop these off since they are passed to this method but we can't
#        # pass them to forms.Form.__init__
#        kwargs.pop("reserved_usernames", [])
#        kwargs.pop("no_duplicate_emails", False)
        
#        super(PinaxOpenIDSignupForm, self).__init__(*args, **kwargs)
#        self.fields["email"].label = "Email"
#        self.fields["email"].required = True


