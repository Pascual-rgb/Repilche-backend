from rest_framework import viewsets, permissions
from Repilche.models import Categoria
from api.serializers import CategorySerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint de solo lectura para las categorías de prendas."""
    queryset = Categoria.objects.all().order_by('nombre')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None