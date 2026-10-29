from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
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
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Notificacion.objects.none()
        return Notificacion.objects.filter(usuario=self.request.user).order_by("-creado_el")

    @action(detail=True, methods=["post", "patch"], url_path="leer")
    def leer(self, request, pk=None):
        """Marca una notificación individual como leída."""
        notificacion = self.get_object()
        notificacion.leida = True
        notificacion.save(update_fields=["leida"])
        return Response(self.get_serializer(notificacion).data)

    @action(detail=True, methods=["post", "patch"], url_path="read")
    def read(self, request, pk=None):
        """Alias para clientes en inglés."""
        return self.leer(request, pk)

    @action(detail=False, methods=["post", "patch"], url_path="leer-todas")
    def leer_todas(self, request):
        """Marca todas las notificaciones no leídas del usuario actual como leídas."""
        actualizadas = self.get_queryset().filter(leida=False).update(leida=True)
        return Response({"status": "ok", "actualizadas": actualizadas}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post", "patch"], url_path="read-all")
    def read_all(self, request):
        """Alias para clientes en inglés."""
        return self.leer_todas(request)
