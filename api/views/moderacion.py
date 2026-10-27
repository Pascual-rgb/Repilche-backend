from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from Repilche.models import Producto, Notificacion
from api.serializers import ModeracionProductoSerializer, RechazarProductoSerializer


class ModeracionProductoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint exclusivo para administradores:
    GET /api/moderation/products/ -> Lista productos en estado 'PENDIENTE' ordenados por antigüedad ascendente.
    POST /api/moderation/products/{id}/approve/ -> Aprueba el producto.
    POST /api/moderation/products/{id}/reject/ -> Rechaza el producto con motivo.
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ModeracionProductoSerializer
    queryset = Producto.objects.filter(estado_moderacion="PENDIENTE").order_by("creado_el")

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        producto = self.get_object()
        
        # Validar si ya fue aprobado previamente
        if producto.estado_moderacion == "APROBADO":
            return Response({"error": "El producto ya se encuentra aprobado."}, status=status.HTTP_400_BAD_REQUEST)

        producto.estado_moderacion = "APROBADO"
        producto.moderado_el = timezone.now()
        producto.motivo_rechazo = ""
        producto.save()

        # Crear notificación al vendedor
        Notificacion.objects.create(
            usuario=producto.vendedor,
            tipo="MODERACION",
            titulo="¡Tu prenda fue aprobada!",
            mensaje=f"Tu prenda '{producto.nombre}' ha sido aprobada y ya está publicada en el catálogo."
        )

        serializer = self.get_serializer(producto)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        producto = self.get_object()
        serializer = RechazarProductoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        motivo = serializer.validated_data["motivo"]
        producto.estado_moderacion = "RECHAZADO"
        producto.motivo_rechazo = motivo
        producto.moderado_el = timezone.now()
        producto.save()

        # Crear notificación al vendedor
        Notificacion.objects.create(
            usuario=producto.vendedor,
            tipo="MODERACION",
            titulo="Tu prenda no fue aprobada",
            mensaje=f"Tu prenda '{producto.nombre}' fue rechazada. Motivo: {motivo}"
        )

        serializer = self.get_serializer(producto)
        return Response(serializer.data, status=status.HTTP_200_OK)