from rest_framework import viewsets, filters
from Repilche.models import Categoria, Producto
from .serializers import CategorySerializer, ProductSerializer

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint de solo lectura para las categorías de prendas."""
    queryset = Categoria.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para listar y consultar productos del e-commerce.
    Incluye búsqueda por nombre/descripción y filtrado por categoría.
    """
    queryset = Producto.objects.filter(estado="DISPONIBLE").select_related('vendedor', 'categoria').order_by('-creado_el')
    serializer_class = ProductSerializer
    
    # Habilitar búsqueda y filtros
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'descripcion', 'vendedor__first_name']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Permitir filtrar por categoría vía query params: /api/productos/?categoria=3
        categoria_id = self.request.query_params.get('categoria')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        return queryset