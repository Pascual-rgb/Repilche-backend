from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from Repilche.models import ItemPedido, Notificacion
from api.serializers import ItemPedidoSerializer


class EntregaVentasViewSet(viewsets.ViewSet):
    """
    GET /api/mis-compras/ -> Muestra ítems comprados por el usuario con su código de 6 dígitos.
    GET /api/mis-ventas/ -> Muestra prendas vendidas y su estado de entrega.
    POST /api/confirmar-entrega/ -> Vendedor ingresa código enviado por el comprador para liberar entrega.
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="mis-compras")
    def mis_compras(self, request):
        user = request.user
        items = ItemPedido.objects.filter(pedido__comprador=user).order_by("-creado_el")
        serializer = ItemPedidoSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="mis-ventas")
    def mis_ventas(self, request):
        user = request.user
        if not hasattr(user, "perfil_vendedor"):
            return Response({"error": "No tienes perfil de vendedor registrado."}, status=status.HTTP_400_BAD_REQUEST)
        
        items = ItemPedido.objects.filter(vendedor=user.perfil_vendedor).order_by("-creado_el")
        serializer = ItemPedidoSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="confirmar-entrega")
    def confirmar_entrega(self, request):
        user = request.user
        if not hasattr(user, "perfil_vendedor"):
            return Response({"error": "Solo un vendedor registrado puede confirmar entregas."}, status=status.HTTP_403_FORBIDDEN)

        codigo = request.data.get("codigo_secreto") or request.data.get("codigo")
        if not codigo:
            return Response({"error": "Debe proporcionar el código secreto de 6 dígitos."}, status=status.HTTP_400_BAD_REQUEST)

        # Buscar el ítem asignado a este vendedor con dicho código secreto
        item = get_object_or_404(ItemPedido, codigo_secreto=codigo, vendedor=user.perfil_vendedor)

        if item.estado_entrega == "entregado":
            return Response({"mensaje": "Este ítem ya fue marcado como entregado anteriormente."}, status=status.HTTP_200_OK)

        item.estado_entrega = "entregado"
        item.save()

        # Notificar al comprador
        comprador = item.pedido.comprador
        Notificacion.objects.create(
            usuario=comprador,
            titulo="¡Entrega Confirmada!",
            mensaje=f"El vendedor confirmó la entrega en mano de '{item.nombre_producto}'. Se han liberado los fondos."
        )

        # Notificar al vendedor
        Notificacion.objects.create(
            usuario=user,
            titulo="Venta Finalizada Exitosamente",
            mensaje=f"Confirmaste la entrega de '{item.nombre_producto}'. Fondos liberados."
        )

        return Response({
            "mensaje": f"Entrega confirmada para '{item.nombre_producto}'.",
            "estado_entrega": item.estado_entrega
        }, status=status.HTTP_200_OK)