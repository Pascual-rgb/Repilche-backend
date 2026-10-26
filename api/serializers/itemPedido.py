from rest_framework import serializers
from Repilche.models import ItemPedido


class ItemPedidoSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPedido
        fields = ["id", "producto", "nombre_producto", "precio_unitario", "cantidad", "subtotal", "codigo_secreto", "estado_entrega"]
        read_only_fields = ["id", "nombre_producto", "precio_unitario", "codigo_secreto"]