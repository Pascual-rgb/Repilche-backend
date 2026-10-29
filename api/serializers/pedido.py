from rest_framework import serializers
from django.db import transaction
from Repilche.models import Carrito, Pedido, ItemPedido, Producto, Notificacion
from Repilche.models.itemPedido import generar_codigo_secreto
from Repilche.notificaciones import notificar
from .itemPedido import ItemPedidoSerializer


class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, read_only=True)
    comprobante = serializers.ImageField(required=False, allow_null=True)
    fecha_creacion = serializers.DateTimeField(source='creado_el', read_only=True)
    estado = serializers.CharField(source='estado_pago', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "comprador",
            "estado_pago",
            "estado",
            "alias_pago",
            "total",
            "comprobante",
            "items",
            "creado_el",
            "fecha_creacion",
        ]
        read_only_fields = ["id", "comprador", "estado_pago", "estado", "total", "creado_el", "fecha_creacion"]

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        carrito = Carrito.objects.filter(usuario=user).first()
        if carrito is None:
            raise serializers.ValidationError("El carrito de compras está vacío.")

        items_carrito = list(carrito.items.select_related("producto").all())
        if not items_carrito:
            raise serializers.ValidationError("No hay ítems en el carrito para procesar el pedido.")

        # Bloquea las filas de las prendas hasta el fin de la transacción para
        # que dos compradores no puedan comprar la misma prenda a la vez.
        producto_ids = [item.producto_id for item in items_carrito]
        productos = {
            p.id: p for p in Producto.objects.select_for_update().filter(id__in=producto_ids)
        }

        errores = []
        for item in items_carrito:
            producto = productos.get(item.producto_id)
            if producto is None:
                errores.append(f"La prenda #{item.producto_id} ya no existe.")
            elif producto.estado != Producto.Estado.DISPONIBLE:
                errores.append(f"La prenda '{producto.nombre}' ya no está disponible.")
            elif producto.estado_moderacion != Producto.EstadoModeracion.APROBADO:
                errores.append(f"La prenda '{producto.nombre}' no está aprobada para la venta.")
            elif producto.vendedor_id == user.id:
                errores.append(f"No podés comprar tu propia prenda '{producto.nombre}'.")
            elif producto.stock < item.cantidad:
                errores.append(f"Stock insuficiente para la prenda: {producto.nombre}")
        if errores:
            raise serializers.ValidationError(errores)

        total = sum(productos[i.producto_id].precio * i.cantidad for i in items_carrito)
        pedido = Pedido.objects.create(
            comprador=user,
            total=total,
            estado_pago=Pedido.EstadoPago.PENDIENTE,
            **validated_data
        )

        for item in items_carrito:
            producto = productos[item.producto_id]
            item_pedido = ItemPedido.objects.create(
                pedido=pedido,
                producto=producto,
                vendedor=producto.vendedor,
                nombre_producto=producto.nombre,
                precio_unitario=producto.precio,
                cantidad=item.cantidad,
                codigo_secreto=generar_codigo_secreto(),
            )

            producto.stock -= item.cantidad
            if producto.stock == 0:
                producto.estado = Producto.Estado.VENDIDO
            producto.save(update_fields=["stock", "estado", "actualizado_el"])

            notificar(
                user,
                "¡Compra realizada!",
                f"Compraste '{producto.nombre}' (Pedido #{pedido.id}). "
                f"Tu código de retiro es {item_pedido.codigo_secreto}. "
                "Dáselo al vendedor solo cuando recibas la prenda.",
                tipo=Notificacion.Tipo.PEDIDO,
            )
            notificar(
                producto.vendedor,
                "¡Vendiste una prenda!",
                f"Se vendió '{producto.nombre}' (Pedido #{pedido.id}). "
                "Coordiná la entrega y pedile al comprador el código de 6 dígitos para confirmarla.",
                tipo=Notificacion.Tipo.PEDIDO,
            )

        carrito.items.all().delete()

        return pedido


class CompraItemHistorialSerializer(serializers.ModelSerializer):
    """Desglose de cada ítem comprado en el historial C2C."""
    item_id = serializers.IntegerField(source="id", read_only=True)
    producto_id = serializers.SerializerMethodField()
    nombre = serializers.CharField(source="nombre_producto", read_only=True)
    precio = serializers.SerializerMethodField()
    imagen = serializers.SerializerMethodField()
    vendedor_id = serializers.SerializerMethodField()
    vendedor_nombre = serializers.SerializerMethodField()
    codigo_secreto = serializers.CharField(read_only=True)
    estado_entrega = serializers.CharField(read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            "id",
            "item_id",
            "producto_id",
            "nombre",
            "nombre_producto",
            "precio",
            "precio_unitario",
            "cantidad",
            "subtotal",
            "imagen",
            "vendedor_id",
            "vendedor_nombre",
            "codigo_secreto",
            "estado_entrega",
        ]

    def get_producto_id(self, obj):
        return obj.producto_id if obj.producto_id else None

    def get_precio(self, obj):
        return float(obj.precio_unitario) if obj.precio_unitario is not None else 0.0

    def get_imagen(self, obj):
        if obj.producto and obj.producto.imagen:
            return obj.producto.imagen
        return ""

    def get_vendedor_id(self, obj):
        return obj.vendedor_id if obj.vendedor_id else None

    def get_vendedor_nombre(self, obj):
        if obj.vendedor:
            name = f"{obj.vendedor.first_name} {obj.vendedor.last_name}".strip()
            return name if name else (obj.vendedor.username or obj.vendedor.email)
        return ""


class CompraHistorialSerializer(serializers.ModelSerializer):
    """
    Serializador de compras agrupadas por pedido para el comprador (GET /api/pedidos/ o /api/mis-compras/).
    Cumple con el contrato exacto de auditoría: pedido_id, fecha, total, estado, items.
    """
    pedido_id = serializers.IntegerField(source="id", read_only=True)
    fecha = serializers.DateTimeField(source="creado_el", read_only=True)
    total = serializers.SerializerMethodField()
    estado = serializers.CharField(source="estado_pago", read_only=True)
    items = CompraItemHistorialSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "pedido_id",
            "fecha",
            "creado_el",
            "total",
            "estado",
            "estado_pago",
            "alias_pago",
            "comprobante",
            "items",
        ]

    def get_total(self, obj):
        return float(obj.total) if obj.total is not None else 0.0