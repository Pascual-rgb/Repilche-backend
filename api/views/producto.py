from rest_framework import viewsets, filters, permissions
from Repilche.models import Producto
from api.serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    Endpoint completo para productos.
    - Lectura pública para cualquier usuario (ReadOnly para listar).
    - Creación/Modificación restringida a usuarios con is_vendedor=True.
    """
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'descripcion', 'vendedor__first_name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        # Tomamos el queryset base optimizado con select_related
        queryset = Producto.objects.select_related('vendedor', 'categoria').order_by('-creado_el')
        
        # Filtrar por productos propios del vendedor si se solicita
        mis_productos = self.request.query_params.get('mis_productos')
        if mis_productos and self.request.user.is_authenticated:
            return queryset.filter(vendedor=self.request.user)
            
        # Si es vista pública del catálogo, mostrar solo los DISPONIBLES
        return queryset.filter(estado="DISPONIBLE")