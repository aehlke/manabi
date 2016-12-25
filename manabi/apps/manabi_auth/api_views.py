from django.contrib.auth import user_logged_in
from djoser.views import RegistrationView
from djoser.utils import login_user


class RegistrationWithTokenView(RegistrationView):
    def perform_create(self, serializer):
        super(RegistrationWithTokenView, self).perform_create(serializer)

        user = serializer.instance
        user_logged_in.send(sender=user.__class__, request=self.request, user=user)
