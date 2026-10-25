from .models import Notificacion


def notificar(usuario, titulo, mensaje, tipo="INFO"):
    """Crea y devuelve una notificación para el usuario indicado."""
    return Notificacion.objects.create(
        usuario=usuario,
        titulo=titulo,
        mensaje=mensaje,
        tipo=tipo,
    )
