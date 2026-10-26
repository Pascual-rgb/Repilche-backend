from rest_framework import serializers
from Repilche.models import ItemCarrito
from .producto import ProductSerializer


class ItemCarritoSerializer(serializers.ModelSerializer):
    producto_detail = ProductSerializer(source='producto', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemCarrito
        fields = ["id", "producto", "producto_detail", "cantidad", "subtotal"]