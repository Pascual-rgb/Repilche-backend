from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from Repilche.models import Carrito, ItemCarrito, Producto
from api.serializers import CarritoSerializer


class CartViewSet(viewsets.ViewSet):
    """
    Endpoint para la gestión del Carrito de Compras del usuario autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_cart(self):
        carrito, _ = Carrito.objects.get_or_create(usuario=self.request.user)
        return carrito

    def list(self, request):
        carrito = self._get_user_cart()
        serializer = CarritoSerializer(carrito)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        carrito = self._get_user_cart()
        producto_id = request.data.get('producto_id') or request.data.get('producto')
        cantidad = int(request.data.get('cantidad', 1))

        producto = get_object_or_404(Producto, id=producto_id, estado="DISPONIBLE")

        if producto.stock < cantidad:
            return Response({"error": "No hay suficiente stock disponible para este producto."}, status=status.HTTP_400_BAD_REQUEST)

        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto, defaults={'cantidad': cantidad})
        if not created:
            nueva_cantidad = item.cantidad + cantidad
            if producto.stock < nueva_cantidad:
                return Response({"error": "La cantidad total excede el stock disponible."}, status=status.HTTP_400_BAD_REQUEST)
            item.cantidad = nueva_cantidad
            item.save()

        serializer = CarritoSerializer(carrito)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch', 'put'])
    def update_item(self, request):
        carrito = self._get_user_cart()
        item_id = request.data.get('item_id')
        cantidad = int(request.data.get('cantidad', 1))

        if cantidad <= 0:
            return Response({"error": "La cantidad debe ser mayor a 0."}, status=status.HTTP_400_BAD_REQUEST)

        item = get_object_or_404(ItemCarrito, id=item_id, carrito=carrito)
        if item.producto.stock < cantidad:
            return Response({"error": "Stock insuficiente."}, status=status.HTTP_400_BAD_REQUEST)

        item.cantidad = cantidad
        item.save()

        serializer = CarritoSerializer(carrito)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        carrito = self._get_user_cart()
        item_id = request.data.get('item_id')

        item = get_object_or_404(ItemCarrito, id=item_id, carrito=carrito)
        item.delete()

        serializer = CarritoSerializer(carrito)
        return Response(serializer.data, status=status.HTTP_200_OK)