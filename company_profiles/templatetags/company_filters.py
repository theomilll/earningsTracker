# company_profiles/templatetags/company_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get dictionary item by key."""
    return dictionary.get(key)