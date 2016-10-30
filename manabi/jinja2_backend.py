from django.template.backends.jinja2 import Jinja2


class ManabiJinja2(Jinja2):
    app_dirname = 'templates'
