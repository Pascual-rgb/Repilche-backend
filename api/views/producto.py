from rest_framework import viewsets, filters, permissions
from Repilche.models import Producto
from api.serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    Endpoint completo para productos.
    - Lectura pública para cualquier usuario (ReadOnly para listar).
    - Creación/Modificación restringida a usuarios con is_vendedor=True.
    """
    queryset = Producto.objects.filter(
        estado=Producto.Estado.DISPONIBLE,
        estado_moderacion=Producto.EstadoModeracion.APROBADO,
    ).select_related('vendedor', 'categoria').order_by('-creado_el')
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'descripcion', 'vendedor__first_name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get('categoria')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)

        mis_productos = self.request.query_params.get('mis_productos')
        if mis_productos and self.request.user.is_authenticated:
            queryset = Producto.objects.filter(vendedor=self.request.user).order_by('-creado_el')

        return queryset