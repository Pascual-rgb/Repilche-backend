from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from Repilche.models import ItemPedido, Notificacion
from Repilche.notificaciones import notificar
from api.serializers import (
    MisComprasItemSerializer,
    MisVentasItemSerializer,
    ConfirmarEntregaSerializer,
    CompraHistorialSerializer,
)


class MisComprasView(generics.ListAPIView):
    """
    Endpoint C2C para el comprador: GET /api/mis-compras/
    - Por defecto retorna los ítems adquiridos por el usuario con su código secreto de retiro.
    - Soporta ?agrupado=true o ?pedidos=true para devolver los pedidos con desglose de ítems.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.query_params.get("agrupado") or self.request.query_params.get("pedidos"):
            return CompraHistorialSerializer
        return MisComprasItemSerializer

    def get_queryset(self):
        if self.request.query_params.get("agrupado") or self.request.query_params.get("pedidos"):
            from Repilche.models import Pedido
            return (
                Pedido.objects.filter(comprador=self.request.user)
                .prefetch_related("items__producto", "items__vendedor")
                .order_by("-creado_el")
            )
        return (
            ItemPedido.objects.filter(pedido__comprador=self.request.user)
            .select_related("pedido", "producto", "vendedor")
            .order_by("-creado_el")
        )


class MisVentasView(generics.ListAPIView):
    """
    Endpoint C2C para el vendedor: GET /api/mis-ventas/
    Lista los ítems vendidos por el usuario autenticado para gestionar sus entregas.
    El código secreto está estrictamente oculto.
    """
    serializer_class = MisVentasItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            ItemPedido.objects.filter(vendedor=self.request.user)
            .select_related("pedido", "producto", "pedido__comprador")
            .order_by("-creado_el")
        )


class ConfirmarEntregaView(APIView):
    """
    Endpoint C2C: POST /api/ventas/<item_id>/confirmar-entrega/
    Permite al vendedor confirmar la entrega de un ítem validando el código
    secreto de 6 dígitos que le entrega el comprador en mano.
    Al confirmar:
    - Cambia el estado_entrega a ENTREGADO.
    - Notifica al vendedor la liberación de fondos.
    - Notifica al comprador que la entrega fue completada.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, item_id=None, pk=None):
        target_id = item_id or pk
        item = get_object_or_404(
            ItemPedido.objects.select_related("pedido", "pedido__comprador", "vendedor", "producto"),
            id=target_id,
        )

        # 1. Permisos: Solo el vendedor del ítem (o staff) puede confirmar la entrega
        if item.vendedor != request.user and not request.user.is_staff:
            return Response(
                {"detail": "No tenés permisos para confirmar la entrega de este ítem."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 2. Validación de estado previo
        if item.estado_entrega == ItemPedido.EstadoEntrega.ENTREGADO:
            return Response(
                {"detail": "Este ítem ya se encuentra marcado como entregado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if item.estado_entrega == ItemPedido.EstadoEntrega.CANCELADO:
            return Response(
                {"detail": "No es posible confirmar la entrega de un ítem cancelado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Validación del código numérico de 6 dígitos
        serializer = ConfirmarEntregaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        codigo_ingresado = serializer.validated_data["codigo"]
        if codigo_ingresado != item.codigo_secreto:
            return Response(
                {"codigo": ["El código de entrega ingresado es incorrecto."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Actualización a ENTREGADO (liberación de fondos)
        item.estado_entrega = ItemPedido.EstadoEntrega.ENTREGADO
        item.save(update_fields=["estado_entrega"])

        # 5. Notificaciones automáticas a comprador y vendedor
        notificar(
            usuario=item.vendedor,
            titulo="¡Entrega confirmada y fondos liberados!",
            mensaje=(
                f"Confirmaste la entrega de '{item.nombre_producto}' (Pedido #{item.pedido_id}). "
                f"Se han liberado los fondos correspondientes (${item.subtotal:.2f})."
            ),
            tipo=Notificacion.Tipo.PEDIDO,
        )

        comprador = item.pedido.comprador
        if comprador:
            notificar(
                usuario=comprador,
                titulo="¡Entrega completada!",
                mensaje=(
                    f"El vendedor confirmó la entrega de '{item.nombre_producto}' (Pedido #{item.pedido_id}). "
                    "¡Gracias por tu compra en Repilche!"
                ),
                tipo=Notificacion.Tipo.PEDIDO,
            )

        return Response(
            {
                "mensaje": "Entrega confirmada exitosamente y fondos liberados.",
                "item": MisVentasItemSerializer(item).data,
            },
            status=status.HTTP_200_OK,
        )
