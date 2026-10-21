from rest_framework import viewsets, filters
from Repilche.models import Category, Product
from .serializers import CategorySerializer, ProductSerializer

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para listar y consultar productos.
    Incluye búsqueda por nombre y filtrado por categoría.
    """
    queryset = Product.objects.all().order_by('-id')
    serializer_class = ProductSerializer
    
    # Habilitar búsqueda y filtrado sencillo
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']  # Ajusta los nombres de los campos de tu modelo