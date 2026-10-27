from rest_framework import serializers
from django.contrib.auth import get_user_model
from Repilche.models import ItemPedido

User = get_user_model()


class C2CUsuarioResumenSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "nombre"]

    def get_nombre(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full if full else obj.email


class MisComprasItemSerializer(serializers.ModelSerializer):
    """
    Serializador para el comprador (GET /api/mis-compras/).
    Expone el código de retiro de 6 dígitos para que el comprador se lo muestre al vendedor.
    """
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    pedido_id = serializers.IntegerField(source="pedido.id", read_only=True)
    producto_id = serializers.IntegerField(source="producto.id", read_only=True)
    vendedor = C2CUsuarioResumenSerializer(read_only=True)
    codigo_secreto = serializers.CharField(read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            "id",
            "pedido_id",
            "producto_id",
            "nombre_producto",
            "precio_unitario",
            "cantidad",
            "subtotal",
            "codigo_secreto",
            "estado_entrega",
            "vendedor",
            "creado_el",
        ]
        read_only_fields = fields


class MisVentasItemSerializer(serializers.ModelSerializer):
    """
    Serializador para el vendedor (GET /api/mis-ventas/).
    OCULTA el código secreto para que el vendedor solo pueda confirmarlo cuando el comprador se lo dé.
    """
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    pedido_id = serializers.IntegerField(source="pedido.id", read_only=True)
    producto_id = serializers.IntegerField(source="producto.id", read_only=True)
    comprador = C2CUsuarioResumenSerializer(source="pedido.comprador", read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            "id",
            "pedido_id",
            "producto_id",
            "nombre_producto",
            "precio_unitario",
            "cantidad",
            "subtotal",
            "estado_entrega",
            "comprador",
            "creado_el",
        ]
        read_only_fields = fields


class ConfirmarEntregaSerializer(serializers.Serializer):
    """
    Validador del código recibido para la confirmación de entrega en mano.
    Acepta tanto 'codigo' como 'codigo_secreto'.
    """
    codigo = serializers.CharField(max_length=10, required=False)
    codigo_secreto = serializers.CharField(max_length=10, required=False)

    def validate(self, attrs):
        codigo = attrs.get("codigo") or attrs.get("codigo_secreto")
        if not codigo or not str(codigo).strip():
            raise serializers.ValidationError({"codigo": "El código de entrega de 6 dígitos es obligatorio."})
        attrs["codigo"] = str(codigo).strip()
        return attrs
