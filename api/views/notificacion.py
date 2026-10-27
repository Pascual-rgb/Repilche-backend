from rest_framework import viewsets, permissions
from Repilche.models import Notificacion
from api.serializers import NotificacionSerializer


class NotificacionViewSet(viewsets.ModelViewSet):
    """
    GET /api/notifications/ -> Listar notificaciones propias ordenadas por fecha descendente.
    PATCH /api/notifications/{id}/ -> Marcar leída con {"leida": True}.
    """
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user).order_by("-creado_el")