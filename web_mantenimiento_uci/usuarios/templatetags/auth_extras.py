from django import template

from usuarios import permisos

register = template.Library()


@register.filter(name='has_groups')
def has_groups(user, group_names):
    """¿El usuario tiene alguno de los roles indicados (separados por comas)?

    Usa los roles efectivos: el superusuario cuenta como «administrador» y
    quien no tiene ningún rol de trabajo cuenta como «cliente» (Solicitante).
    """
    nombres = {nombre.strip() for nombre in str(group_names).split(',') if nombre.strip()}
    return bool(permisos.roles_de(user) & nombres)


@register.filter(name='nombre_rol')
def nombre_rol(codigo):
    """'cliente' -> 'Solicitante', 'tecnico' -> 'Técnico'…"""
    return permisos.nombre_rol(codigo)


@register.filter(name='roles_texto')
def roles_texto(user):
    """Roles de un usuario tal como se muestran: «Administrador», «Solicitante»…"""
    return permisos.roles_texto(user)
