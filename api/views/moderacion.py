from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from Repilche.models import Producto
from Repilche.notificaciones import notificar
from api.serializers import ProductSerializer


class ModeracionProductoViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Permite a los administradores moderar prendas pendientes."""
    queryset = Producto.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        if self.action == "list":
            return Producto.objects.filter(
                estado_moderacion="PENDIENTE"
            ).order_by("creado_el")
        return Producto.objects.all()

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def approve(self, request, pk=None):
        producto = self.get_object()
        if producto.estado_moderacion != "PENDIENTE":
            return Response(
                {"error": "Solo se pueden aprobar prendas pendientes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        producto.estado_moderacion = "APROBADO"
        producto.moderado_el = timezone.now()
        producto.motivo_rechazo = ""
        producto.save(update_fields=["estado_moderacion", "moderado_el", "motivo_rechazo"])
        notificar(
            producto.vendedor,
            "Prenda aprobada",
            f'Tu prenda "{producto.nombre}" ya está publicada en Repilche.',
            tipo="MODERACION",
        )
        return Response(self.get_serializer(producto).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def reject(self, request, pk=None):
        motivo = request.data.get("motivo", "")
        if not isinstance(motivo, str) or not motivo.strip():
            return Response(
                {"motivo": ["Este campo es obligatorio."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        producto = self.get_object()
        producto.estado_moderacion = "RECHAZADO"
        producto.motivo_rechazo = motivo.strip()
        producto.moderado_el = timezone.now()
        producto.save(update_fields=["estado_moderacion", "motivo_rechazo", "moderado_el"])
        notificar(
            producto.vendedor,
            "Prenda rechazada",
            f'Tu prenda "{producto.nombre}" fue rechazada. Motivo: {producto.motivo_rechazo}',
            tipo="MODERACION",
        )
        return Response(self.get_serializer(producto).data)
