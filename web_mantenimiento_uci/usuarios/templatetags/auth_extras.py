from django import template

register = template.Library()

@register.filter(name='has_groups')
def has_groups(user, group_names):
    """Verifica si el usuario está en al menos uno de los grupos."""
    return user.groups.filter(name__in=group_names.split(',')).exists()