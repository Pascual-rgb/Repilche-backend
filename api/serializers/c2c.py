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
    item_id = serializers.IntegerField(source="id", read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    pedido_id = serializers.IntegerField(source="pedido.id", read_only=True)
    producto_id = serializers.IntegerField(source="producto.id", read_only=True)
    nombre = serializers.CharField(source="nombre_producto", read_only=True)
    precio = serializers.SerializerMethodField()
    imagen = serializers.SerializerMethodField()
    vendedor_id = serializers.IntegerField(source="vendedor.id", read_only=True)
    vendedor_nombre = serializers.SerializerMethodField()
    vendedor = C2CUsuarioResumenSerializer(read_only=True)
    codigo_secreto = serializers.CharField(read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            "id",
            "item_id",
            "pedido_id",
            "producto_id",
            "nombre",
            "nombre_producto",
            "precio",
            "precio_unitario",
            "cantidad",
            "subtotal",
            "imagen",
            "codigo_secreto",
            "estado_entrega",
            "vendedor",
            "vendedor_id",
            "vendedor_nombre",
            "creado_el",
        ]
        read_only_fields = fields

    def get_precio(self, obj):
        return float(obj.precio_unitario) if obj.precio_unitario is not None else 0.0

    def get_imagen(self, obj):
        if obj.producto and obj.producto.imagen:
            return obj.producto.imagen
        return ""

    def get_vendedor_nombre(self, obj):
        if obj.vendedor:
            name = f"{obj.vendedor.first_name} {obj.vendedor.last_name}".strip()
            return name if name else (obj.vendedor.username or obj.vendedor.email)
        return ""


class MisVentasItemSerializer(serializers.ModelSerializer):
    """
    Serializador para el vendedor (GET /api/mis-ventas/ o /api/ventas/).
    OCULTA el código secreto para que el vendedor solo pueda confirmarlo cuando el comprador se lo dé.
    """
    item_id = serializers.IntegerField(source="id", read_only=True)
    pedido_id = serializers.IntegerField(source="pedido.id", read_only=True)
    fecha = serializers.DateTimeField(source="creado_el", read_only=True)
    producto_id = serializers.IntegerField(source="producto.id", read_only=True)
    nombre = serializers.CharField(source="nombre_producto", read_only=True)
    precio = serializers.SerializerMethodField()
    imagen = serializers.SerializerMethodField()
    comprador_nombre = serializers.SerializerMethodField()
    comprador_telefono = serializers.SerializerMethodField()
    comprador = C2CUsuarioResumenSerializer(source="pedido.comprador", read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            "id",
            "item_id",
            "pedido_id",
            "fecha",
            "producto_id",
            "nombre",
            "nombre_producto",
            "precio",
            "precio_unitario",
            "cantidad",
            "subtotal",
            "imagen",
            "comprador_nombre",
            "comprador_telefono",
            "estado_entrega",
            "comprador",
            "creado_el",
        ]
        read_only_fields = fields

    def get_precio(self, obj):
        return float(obj.precio_unitario) if obj.precio_unitario is not None else 0.0

    def get_imagen(self, obj):
        if obj.producto and obj.producto.imagen:
            return obj.producto.imagen
        return ""

    def get_comprador_nombre(self, obj):
        if obj.pedido and obj.pedido.comprador:
            u = obj.pedido.comprador
            full = f"{u.first_name} {u.last_name}".strip()
            return full if full else (u.username or u.email)
        return ""

    def get_comprador_telefono(self, obj):
        if obj.pedido and obj.pedido.comprador:
            return getattr(obj.pedido.comprador, "phone", "") or getattr(obj.pedido.comprador, "celphone", "") or ""
        return ""


class ConfirmarEntregaSerializer(serializers.Serializer):
    """
    Validador del código recibido para la confirmación de entrega en mano.
    Acepta tanto 'codigo' como 'codigo_secreto', e 'item_id'.
    """
    item_id = serializers.IntegerField(required=False)
    codigo = serializers.CharField(max_length=20, required=False)
    codigo_secreto = serializers.CharField(max_length=20, required=False)

    def validate(self, attrs):
        codigo = attrs.get("codigo") or attrs.get("codigo_secreto")
        if not codigo or not str(codigo).strip():
            raise serializers.ValidationError({"codigo": "El código de entrega de 6 dígitos es obligatorio."})
        attrs["codigo"] = str(codigo).strip()
        return attrs
