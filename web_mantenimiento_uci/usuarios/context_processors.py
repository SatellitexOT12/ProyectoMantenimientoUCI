from . import permisos


def roles(request):
    """Roles y capacidades del usuario en TODAS las plantillas.

    Claves (solo con sesión iniciada; sin sesión no añade nada):
      is_admin, is_tecnico, is_almacenero, is_cliente : bool
      rol_display : texto («Administrador», «Solicitante», «Técnico, Almacenero»…)
      puede : dict de bool para decidir qué enlaces mostrar (ver el contrato)

    Las vistas que ya definen ``is_*`` en su contexto tienen prioridad, con
    los mismos valores.
    """
    usuario = getattr(request, 'user', None)
    if usuario is None or not usuario.is_authenticated:
        return {}
    return {
        'is_admin': permisos.es_administrador(usuario),
        'is_tecnico': permisos.es_tecnico(usuario),
        'is_almacenero': permisos.es_almacenero(usuario),
        'is_cliente': permisos.es_solicitante(usuario),
        'rol_display': permisos.roles_texto(usuario),
        'puede': permisos.capacidades(usuario),
    }
