from django.conf import settings
from django.conf.urls import *
from manabi.apps.utils.views import direct_to_template
from .forms import SignupForm


urlpatterns = [
    url(r'^signup/$', 'manabi.apps.stats.views.signup', name='mobile_acct_signup', kwargs={
        'template_name': 'mobileaccount/signup.html',
        #'success_url': 'mobile_account/signup_success.html',
        'form_class': SignupForm}),
]
