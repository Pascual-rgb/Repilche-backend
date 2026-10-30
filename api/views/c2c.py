from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from Repilche.models import ItemPedido, Notificacion, Pedido
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
    Endpoint C2C: 
    - POST /api/pedidos/validar-entrega/ (item_id y codigo en body)
    - POST /api/ventas/<item_id>/confirmar-entrega/ (item_id en url)
    Permite al vendedor confirmar la entrega de un ítem validando el código
    secreto de 6 dígitos que le entrega el comprador en mano.
    Al confirmar:
    - Cambia el estado_entrega a ENTREGADO.
    - Si todos los ítems fueron entregados, actualiza el Pedido a PAGADO/ENTREGADO.
    - Notifica al vendedor la liberación de fondos.
    - Notifica al comprador que la entrega fue completada.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, item_id=None, pk=None):
        target_id = item_id or pk or request.data.get("item_id") or request.data.get("id")
        if not target_id:
            return Response(
                {"error": "Debe proporcionar el identificador del ítem (item_id).", "detail": "El item_id es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            item = ItemPedido.objects.select_related("pedido", "pedido__comprador", "vendedor", "producto").get(id=target_id)
        except (ItemPedido.DoesNotExist, ValueError):
            return Response(
                {"error": "El ítem de pedido no existe.", "detail": "No se encontró el ítem especificado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 1. Permisos: Solo el vendedor del ítem (o staff) puede confirmar la entrega
        if item.vendedor != request.user and not request.user.is_staff:
            return Response(
                {"error": "No tenés permisos para confirmar la entrega de este ítem.", "detail": "No tenés permisos para confirmar la entrega de este ítem."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 2. Validación de estado previo
        if item.estado_entrega == ItemPedido.EstadoEntrega.ENTREGADO:
            return Response(
                {"error": "Este ítem ya fue marcado como entregado.", "detail": "Este ítem ya se encuentra marcado como entregado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if item.estado_entrega == ItemPedido.EstadoEntrega.CANCELADO:
            return Response(
                {"error": "No es posible confirmar la entrega de un ítem cancelado.", "detail": "No es posible confirmar la entrega de un ítem cancelado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Validación del código numérico de 6 dígitos
        serializer = ConfirmarEntregaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        codigo_ingresado = serializer.validated_data["codigo"]
        if str(codigo_ingresado).strip() != str(item.codigo_secreto).strip():
            return Response(
                {
                    "error": "Código de retiro incorrecto. Verifícalo con el comprador.",
                    "codigo": ["El código de entrega ingresado es incorrecto."],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Actualización a ENTREGADO (liberación de fondos)
        item.estado_entrega = ItemPedido.EstadoEntrega.ENTREGADO
        item.save(update_fields=["estado_entrega"])

        # 5. Si todos los ítems del pedido fueron entregados, actualizar el Pedido
        if item.pedido:
            todos_entregados = not item.pedido.items.exclude(id=item.id).exclude(
                estado_entrega=ItemPedido.EstadoEntrega.ENTREGADO
            ).exists()
            if todos_entregados:
                item.pedido.estado_pago = Pedido.EstadoPago.PAGADO
                item.pedido.save(update_fields=["estado_pago", "actualizado_el"])

        # 6. Notificaciones automáticas a comprador y vendedor
        notificar(
            usuario=item.vendedor,
            titulo="¡Entrega confirmada y fondos liberados!",
            mensaje=(
                f"Confirmaste la entrega de '{item.nombre_producto}' (Pedido #{item.pedido_id}). "
                f"Se han liberado los fondos correspondientes (${item.subtotal:.2f})."
            ),
            tipo=Notificacion.Tipo.PEDIDO,
        )

        comprador = item.pedido.comprador if item.pedido else None
        if comprador:
            notificar(
                usuario=comprador,
                titulo="¡Tu prenda fue entregada!",
                mensaje=(
                    f"El vendedor confirmó la entrega de '{item.nombre_producto}' (Pedido #{item.pedido_id}). "
                    "¡Gracias por tu compra en Repilche!"
                ),
                tipo=Notificacion.Tipo.PEDIDO,
            )

        return Response(
            {
                "mensaje": "Entrega confirmada con éxito. Fondos liberados para liquidación.",
                "item": MisVentasItemSerializer(item).data,
            },
            status=status.HTTP_200_OK,
        )
