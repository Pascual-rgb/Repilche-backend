from rest_framework import serializers
from Repilche.models import Carrito
from .itemCarrito import ItemCarritoSerializer


class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Carrito
        fields = ["id", "usuario", "items", "total", "total_items", "actualizado_el"]
        read_only_fields = ["id", "usuario"]