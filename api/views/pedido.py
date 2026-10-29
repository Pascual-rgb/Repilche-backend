from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.conf import settings
from django.db import transaction
from Repilche.models import Pedido, Producto, ItemPedido, Notificacion
from Repilche.models.itemPedido import generar_codigo_secreto
from Repilche.notificaciones import notificar
from api.serializers import PedidoSerializer, CompraHistorialSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Creación y Consulta de Órdenes / Checkout.
    Soporta:
    - Compra directa C2C (POST con {'producto_id': <id>})
    - Checkout por carrito de compras (POST estándar)
    - Historial de compras (GET con desglose exacto de ítems)
    """
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CompraHistorialSerializer
        return PedidoSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return (
                Pedido.objects.all()
                .prefetch_related("items__producto", "items__vendedor")
                .order_by("-creado_el")
            )
        return (
            Pedido.objects.filter(comprador=user)
            .prefetch_related("items__producto", "items__vendedor")
            .order_by("-creado_el")
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        # 1. Detectar si es compra directa unitaria (C2C)
        producto_id = data.get("producto_id") or data.get("producto")
        if not producto_id and isinstance(data.get("productos"), list) and len(data.get("productos")) == 1:
            producto_id = data.get("productos")[0]

        if producto_id:
            try:
                # select_for_update para bloquear la fila y evitar compras concurrentes duplicadas
                producto = (
                    Producto.objects.select_for_update()
                    .select_related("vendedor")
                    .get(id=producto_id)
                )
            except (Producto.DoesNotExist, ValueError):
                return Response(
                    {"error": "El producto no existe."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validar disponibilidad
            if (
                producto.estado != Producto.Estado.DISPONIBLE
                or producto.stock <= 0
            ):
                return Response(
                    {"error": "El producto ya no está disponible"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validar moderación
            if producto.estado_moderacion != Producto.EstadoModeracion.APROBADO:
                return Response(
                    {"error": "El producto no está aprobado para la venta."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validar que no sea su propia prenda
            if producto.vendedor_id == user.id:
                return Response(
                    {"error": "Un vendedor no puede comprar su propia prenda."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Crear Pedido
            pedido = Pedido.objects.create(
                comprador=user,
                total=producto.precio,
                estado_pago=Pedido.EstadoPago.PENDIENTE,
            )

            # Crear ItemPedido
            codigo_secreto = generar_codigo_secreto()
            item_pedido = ItemPedido.objects.create(
                pedido=pedido,
                producto=producto,
                vendedor=producto.vendedor,
                nombre_producto=producto.nombre,
                precio_unitario=producto.precio,
                cantidad=1,
                codigo_secreto=codigo_secreto,
                estado_entrega=ItemPedido.EstadoEntrega.EN_CUSTODIA,
            )

            # Marcar prenda como vendida e indisponible
            producto.stock = 0
            producto.estado = Producto.Estado.VENDIDO
            producto.save(update_fields=["stock", "estado", "actualizado_el"])

            # Notificaciones C2C
            notificar(
                user,
                "¡Compra realizada!",
                (
                    f"Compraste '{producto.nombre}' (Pedido #{pedido.id}). "
                    f"Tu código de retiro es {codigo_secreto}. "
                    "Dáselo al vendedor solo cuando recibas la prenda."
                ),
                tipo=Notificacion.Tipo.PEDIDO,
            )
            notificar(
                producto.vendedor,
                "¡Vendiste una prenda!",
                (
                    f"Se vendió '{producto.nombre}' (Pedido #{pedido.id}). "
                    "Coordiná la entrega y pedile al comprador el código de 6 dígitos para confirmarla."
                ),
                tipo=Notificacion.Tipo.PEDIDO,
            )

            # Retornar respuesta exacta requerida por el contrato
            return Response(
                {
                    "id": pedido.id,
                    "mensaje": "Compra realizada con éxito",
                    "producto": {
                        "id": producto.id,
                        "nombre": producto.nombre,
                    },
                    "total": float(pedido.total),
                    "codigo_secreto": codigo_secreto,
                    "alias_transferencia": getattr(settings, "REPILCHE_ALIAS_PAGO", "repilche.oficial.mp"),
                    "titular": getattr(settings, "REPILCHE_TITULAR_PAGO", "Repilche Moda Circular"),
                    "cbu_cvu": getattr(settings, "REPILCHE_CBU_CVU", "0000003100012345678901"),
                    "estado": str(pedido.estado),
                },
                status=status.HTTP_201_CREATED,
            )

        # 2. Si no se especificó producto_id, delegar al flujo de carrito
        return super().create(request, *args, **kwargs)