from django import template
register = template.Library()

@register.filter
def getitem(d, key):
    if isinstance(d, dict):
        return d.get(key, key)
    return key
