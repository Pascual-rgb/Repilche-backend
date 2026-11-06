from rest_framework import serializers
from Repilche.models import Pedido, ItemPedido, Producto
from .categoria import CategorySerializer


class AdminItemPedidoSerializer(serializers.ModelSerializer):
    producto_id = serializers.SerializerMethodField()
    producto_nombre = serializers.SerializerMethodField()
    producto_imagen = serializers.SerializerMethodField()
    precio = serializers.SerializerMethodField()
    vendedor = serializers.SerializerMethodField()

    class Meta:
        model = ItemPedido
        fields = [
            "id",
            "producto_id",
            "producto_nombre",
            "producto_imagen",
            "precio",
            "precio_unitario",
            "cantidad",
            "subtotal",
            "codigo_secreto",
            "estado_entrega",
            "vendedor",
            "creado_el",
        ]

    def get_producto_id(self, obj):
        return obj.producto_id or (obj.producto.id if obj.producto else None)

    def get_producto_nombre(self, obj):
        return obj.nombre_producto or (obj.producto.nombre if obj.producto else "")

    def get_producto_imagen(self, obj):
        if obj.producto and obj.producto.imagen:
            return obj.producto.imagen.split(",")[0].strip()
        return ""

    def get_precio(self, obj):
        return float(obj.precio_unitario) if obj.precio_unitario is not None else 0.0

    def get_vendedor(self, obj):
        v = obj.vendedor
        if not v:
            return {
                "id": None,
                "nombre": "Repilche Oficial",
                "email": "",
                "telefono": "",
            }
        nombre = f"{v.first_name} {v.last_name}".strip() or v.username or v.email
        telefono = getattr(v, "phone", "") or getattr(v, "celphone", "") or ""
        return {
            "id": v.id,
            "nombre": nombre,
            "email": v.email,
            "telefono": telefono,
        }


class AdminPedidoSerializer(serializers.ModelSerializer):
    fecha = serializers.DateTimeField(source="creado_el", read_only=True)
    total = serializers.SerializerMethodField()
    comprador = serializers.SerializerMethodField()
    items = AdminItemPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "creado_el",
            "fecha",
            "total",
            "estado_pago",
            "alias_pago",
            "comprobante",
            "comprador",
            "items",
            "actualizado_el",
        ]

    def get_total(self, obj):
        return float(obj.total) if obj.total is not None else 0.0

    def get_comprador(self, obj):
        u = obj.comprador
        if not u:
            return None
        nombre = f"{u.first_name} {u.last_name}".strip() or u.username or u.email
        telefono = getattr(u, "phone", "") or getattr(u, "celphone", "") or ""
        return {
            "id": u.id,
            "nombre": nombre,
            "email": u.email,
            "telefono": telefono,
        }


class AdminProductSerializer(serializers.ModelSerializer):
    categoria_detail = CategorySerializer(source='categoria', read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True, default='')
    vendedor_nombre = serializers.SerializerMethodField()
    imagen_url = serializers.CharField(source='imagen', read_only=True)
    img = serializers.CharField(source='imagen', read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id",
            "vendedor",
            "vendedor_nombre",
            "categoria",
            "categoria_nombre",
            "categoria_detail",
            "nombre",
            "descripcion",
            "precio",
            "stock",
            "imagen",
            "imagen_url",
            "img",
            "estado",
            "estado_moderacion",
            "motivo_rechazo",
            "moderado_el",
            "creado_el",
            "actualizado_el",
        ]
        read_only_fields = [
            "id",
            "creado_el",
            "actualizado_el",
        ]

    def get_vendedor_nombre(self, obj):
        if not obj.vendedor:
            return "Repilche Oficial"
        nombre = f"{obj.vendedor.first_name} {obj.vendedor.last_name}".strip()
        return nombre if nombre else (obj.vendedor.username or obj.vendedor.email)

