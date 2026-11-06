from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response

from Repilche.models import Pedido, ItemPedido, Producto, Notificacion
from Repilche.notificaciones import notificar
from api.serializers.admin_ops import (
    AdminPedidoSerializer,
    AdminItemPedidoSerializer,
    AdminProductSerializer,
)
from .producto import CatalogoPagination


class AdminPedidoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Panel Administrativo: Monitoreo y control operativo de Pedidos.
    GET /api/admin/pedidos/
    GET /api/admin/pedidos/<id>/
    POST /api/admin/pedidos/<id>/confirmar-pago/
    POST /api/admin/pedidos/<id>/cancelar/
    """
    queryset = (
        Pedido.objects.all()
        .select_related("comprador")
        .prefetch_related("items__producto", "items__vendedor")
        .order_by("-creado_el")
    )
    serializer_class = AdminPedidoSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = CatalogoPagination

    @action(detail=True, methods=["post"], url_path="confirmar-pago")
    @transaction.atomic
    def confirmar_pago(self, request, pk=None):
        pedido = self.get_object()
        pedido.estado_pago = Pedido.EstadoPago.PAGADO
        pedido.save(update_fields=["estado_pago", "actualizado_el"])

        # Notificar al comprador
        if pedido.comprador:
            notificar(
                usuario=pedido.comprador,
                titulo="¡Pago Confirmado!",
                mensaje=f"Tu pago para el pedido #{pedido.id} por ${pedido.total} ha sido verificado con éxito.",
                tipo=Notificacion.Tipo.PEDIDO,
            )

        # Notificar a los vendedores de cada ítem
        for item in pedido.items.select_related("vendedor").all():
            if item.vendedor:
                notificar(
                    usuario=item.vendedor,
                    titulo="Pago de Pedido Confirmado",
                    mensaje=f"Se confirmó el pago del pedido #{pedido.id} ({item.nombre_producto}). Ya podés coordinar la entrega con el comprador.",
                    tipo=Notificacion.Tipo.PEDIDO,
                )

        return Response(
            {
                "mensaje": f"Pago del pedido #{pedido.id} confirmado con éxito.",
                "pedido": self.get_serializer(pedido).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="cancelar")
    @transaction.atomic
    def cancelar(self, request, pk=None):
        pedido = self.get_object()
        pedido.estado_pago = Pedido.EstadoPago.CANCELADO
        pedido.save(update_fields=["estado_pago", "actualizado_el"])

        # Cancelar ítems y reponer stock
        for item in pedido.items.select_related("producto", "vendedor").all():
            item.estado_entrega = ItemPedido.EstadoEntrega.CANCELADO
            item.save(update_fields=["estado_entrega"])

            if item.producto:
                item.producto.stock = 1
                item.producto.estado = Producto.Estado.DISPONIBLE
                item.producto.save(update_fields=["stock", "estado", "actualizado_el"])

            if item.vendedor:
                notificar(
                    usuario=item.vendedor,
                    titulo="Pedido Cancelado",
                    mensaje=f"El pedido #{pedido.id} ({item.nombre_producto}) fue cancelado y la prenda volvió a estar disponible en el catálogo.",
                    tipo=Notificacion.Tipo.PEDIDO,
                )

        if pedido.comprador:
            notificar(
                usuario=pedido.comprador,
                titulo="Pedido Cancelado",
                mensaje=f"Tu pedido #{pedido.id} ha sido cancelado por la administración.",
                tipo=Notificacion.Tipo.PEDIDO,
            )

        return Response(
            {
                "mensaje": f"Pedido #{pedido.id} cancelado con éxito y stock restituido.",
                "pedido": self.get_serializer(pedido).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminForzarEntregaItemView(APIView):
    """
    POST /api/admin/pedidos/items/<item_id>/forzar-entrega/
    Permite al admin liberar la custodia y cambiar el ItemPedido a ENTREGADO
    en caso de pérdida de código o resolución manual de disputas.
    """
    permission_classes = [permissions.IsAdminUser]

    @transaction.atomic
    def post(self, request, item_id=None, pk=None):
        target_id = item_id or pk or request.data.get("item_id")
        item = get_object_or_404(
            ItemPedido.objects.select_related("pedido", "pedido__comprador", "vendedor", "producto"),
            id=target_id,
        )

        item.estado_entrega = ItemPedido.EstadoEntrega.ENTREGADO
        item.save(update_fields=["estado_entrega"])

        # Si todos los ítems del pedido fueron completados, marcar pedido como PAGADO
        if item.pedido:
            todos_entregados = not item.pedido.items.exclude(id=item.id).exclude(
                estado_entrega=ItemPedido.EstadoEntrega.ENTREGADO
            ).exists()
            if todos_entregados and item.pedido.estado_pago != Pedido.EstadoPago.PAGADO:
                item.pedido.estado_pago = Pedido.EstadoPago.PAGADO
                item.pedido.save(update_fields=["estado_pago", "actualizado_el"])

        # Notificar a las partes
        if item.vendedor:
            notificar(
                usuario=item.vendedor,
                titulo="¡Entrega liberada por administración!",
                mensaje=f"La administración confirmó la entrega de '{item.nombre_producto}' (Pedido #{item.pedido_id}). Fondos liberados (${item.subtotal:.2f}).",
                tipo=Notificacion.Tipo.PEDIDO,
            )

        if item.pedido and item.pedido.comprador:
            notificar(
                usuario=item.pedido.comprador,
                titulo="Entrega confirmada",
                mensaje=f"Se confirmó administrativamente la entrega de '{item.nombre_producto}' (Pedido #{item.pedido_id}).",
                tipo=Notificacion.Tipo.PEDIDO,
            )

        return Response(
            {
                "mensaje": f"Entrega del ítem #{item.id} ({item.nombre_producto}) confirmada administrativamente.",
                "item": AdminItemPedidoSerializer(item).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminProductViewSet(viewsets.ModelViewSet):
    """
    Panel Administrativo: Gestión integral de prendas del catálogo.
    GET /api/admin/products/
    GET /api/admin/products/<id>/
    PATCH /api/admin/products/<id>/
    PUT /api/admin/products/<id>/
    DELETE /api/admin/products/<id>/ (despublicación lógica o hard delete si ?hard=true)
    """
    queryset = Producto.objects.all().select_related("vendedor", "categoria").order_by("-creado_el")
    serializer_class = AdminProductSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = CatalogoPagination

    def destroy(self, request, *args, **kwargs):
        producto = self.get_object()
        hard = request.query_params.get("hard", "").lower() in ("true", "1")
        if hard:
            producto.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        # Despublicación / eliminación lógica
        producto.stock = 0
        producto.estado = Producto.Estado.PAUSADO
        producto.save(update_fields=["stock", "estado", "actualizado_el"])

        return Response(
            {
                "mensaje": f"Prenda '{producto.nombre}' despublicada exitosamente.",
                "id": producto.id,
                "estado": producto.estado,
                "stock": producto.stock,
            },
            status=status.HTTP_200_OK,
        )

