from rest_framework import serializers
from Repilche.models import ItemPedido


class ItemPedidoSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    vendedor_id = serializers.IntegerField(source='vendedor.id', read_only=True)
    vendedor_nombre = serializers.CharField(source='vendedor.usuario.get_full_name', read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            "id",
            "vendedor",
            "vendedor_id",
            "vendedor_nombre",
            "producto",
            "nombre_producto",
            "precio_unitario",
            "cantidad",
            "subtotal",
            "codigo_secreto",
            "estado_entrega",
        ]
        read_only_fields = ["id", "vendedor", "nombre_producto", "precio_unitario", "codigo_secreto"]