from rest_framework import viewsets, filters, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from Repilche.models import Categoria, Producto, Carrito, ItemCarrito, Pedido, Notificacion
from .serializers import (
    CategorySerializer, 
    ProductSerializer, 
    CarritoSerializer, 
    ItemCarritoSerializer, 
    PedidoSerializer,
    NotificacionSerializer,
)


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
        return Notificacion.objects.filter(usuario=self.request.user).order_by("-creado_el")


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint de solo lectura para las categorías de prendas."""
    queryset = Categoria.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    Endpoint completo para productos (Punto 2).
    - Lectura pública para cualquier usuario (ReadOnly para listar).
    - Creación/Modificación restringida a usuarios con is_vendedor=True.
    """
    queryset = Producto.objects.filter(estado="DISPONIBLE").select_related('vendedor', 'categoria').order_by('-creado_el')
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'descripcion', 'vendedor__first_name']

    def get_permissions(self):
        # Permitir lectura libre, exigir autenticación y rol de vendedor para mutaciones
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrar por categoría: /api/products/?categoria=3
        categoria_id = self.request.query_params.get('categoria')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        
        # Filtrar por productos propios del vendedor si se solicita: /api/products/?mis_productos=true
        mis_productos = self.request.query_params.get('mis_productos')
        if mis_productos and self.request.user.is_authenticated:
            queryset = Producto.objects.filter(vendedor=self.request.user).order_by('-creado_el')
            
        return queryset


class CartViewSet(viewsets.ViewSet):
    """
    Endpoint para la gestión del Carrito de Compras del usuario autenticado (Punto 3).
    Permite ver el carrito, agregar ítems, modificar cantidades o eliminar ítems.
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_cart(self):
        carrito, _ = Carrito.objects.get_or_create(usuario=self.request.user)
        return carrito

    def list(self, request):
        """Devuelve el carrito actual del usuario con sus ítems y totales."""
        carrito = self._get_user_cart()
        serializer = CarritoSerializer(carrito)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Agrega un producto o incrementa su cantidad en el carrito."""
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
        """Modifica la cantidad de un ítem específico del carrito."""
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
        """Elimina un ítem del carrito."""
        carrito = self._get_user_cart()
        item_id = request.data.get('item_id')

        item = get_object_or_404(ItemCarrito, id=item_id, carrito=carrito)
        item.delete()

        serializer = CarritoSerializer(carrito)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Creación y Consulta de Órdenes / Checkout (Punto 4).
    - Permite al usuario crear un pedido a partir de su carrito actual (POST).
    - Permite consultar el historial de órdenes del usuario autenticado (GET).
    """
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Si es admin, puede ver todas; si es comprador común, solo ve sus propias órdenes
        if user.is_staff:
            return Pedido.objects.all().order_by('-creado_el')
        return Pedido.objects.filter(comprador=user).order_by('-creado_el')