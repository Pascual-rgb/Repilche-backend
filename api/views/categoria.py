from rest_framework import viewsets
from Repilche.models import Categoria
from api.serializers import CategorySerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint de solo lectura para las categorías de prendas."""
    queryset = Categoria.objects.all()
    serializer_class = CategorySerializer