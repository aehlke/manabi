from django import template

register = template.Library()


@register.simple_tag
def xhrlink(url, text):
    return '<a href="{url}" onclick="manabi_ui.xhrLink(this.href);return false;">{text}</a>'.format(url=url, text=text)

@register.simple_tag
def xhrlink_onclick():
    return 'onclick="manabi_ui.xhrLink(this.href);return false;"'
