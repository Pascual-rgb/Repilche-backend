from rest_framework import serializers
from django.db import transaction
from Repilche.models import Carrito, Pedido, ItemPedido, Producto, Notificacion
from Repilche.models.itemPedido import generar_codigo_secreto
from Repilche.notificaciones import notificar
from .itemPedido import ItemPedidoSerializer


class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, read_only=True)
    comprobante = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "comprador",
            "estado_pago",
            "alias_pago",
            "total",
            "comprobante",
            "items",
            "creado_el",
        ]
        read_only_fields = ["id", "comprador", "estado_pago", "total", "creado_el"]

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
<<<<<<< HEAD
            # Obtener el perfil de vendedor asociado al dueño del producto
            perfil_vendedor = getattr(item.producto.vendedor, 'perfil_vendedor', None)
            
            ItemPedido.objects.create(
                pedido=pedido,
                vendedor=perfil_vendedor,  # <--- CAMPO OBLIGATORIO AGREGADO
                producto=item.producto,
                nombre_producto=item.producto.nombre,
                precio_unitario=item.producto.precio,
                cantidad=item.cantidad
            )
            item.producto.stock -= item.cantidad
            # Si el stock llega a 0, podrías pasarlo a VENDIDO si corresponde
            if item.producto.stock == 0:
                item.producto.estado = "vendido"
            item.producto.save()
            
        items_carrito.delete()
=======
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
>>>>>>> 31e1b1cdfd6ff718db8e2774b695f6b86e83e0e3

        return pedido