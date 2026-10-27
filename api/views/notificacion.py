from rest_framework import viewsets, permissions, mixins
from Repilche.models import Notificacion
from api.serializers import NotificacionSerializer


class NotificacionViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Permite listar y marcar como leídas las notificaciones propias."""
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Notificacion.objects.none()
        return Notificacion.objects.filter(usuario=self.request.user).order_by("-creado_el")
