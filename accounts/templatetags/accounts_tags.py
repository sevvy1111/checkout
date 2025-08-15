# accounts/templatetags/accounts_tags.py
from django import template

register = template.Library()


@register.filter(name='render_field')
def render_field(field, attrs):
    # attrs will be a string like "class:form-control,id:some-id"
    # We parse it into a dictionary
    attr_dict = {}
    for attr in attrs.split(','):
        key, value = attr.split(':')
        attr_dict[key.strip()] = value.strip()

    # Update the widget's attributes
    field.field.widget.attrs.update(attr_dict)
    return field