from rest_framework import viewsets, permissions
from Repilche.models import Pedido
from api.serializers import PedidoSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Creación y Consulta de Órdenes / Checkout.
    """
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Pedido.objects.all().order_by('-creado_el')
        return Pedido.objects.filter(comprador=user).order_by('-creado_el')