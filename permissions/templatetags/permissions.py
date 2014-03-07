"""
Dynamically create template filters for every can_* permission in the
perms module that accepts one or two arguments.
"""
from django import template
register = template.Library()
