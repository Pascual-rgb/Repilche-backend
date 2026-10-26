from rest_framework import serializers
from django.db import transaction
from Repilche.models import Carrito, Pedido, ItemPedido
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
        try:
            carrito = Carrito.objects.get(usuario=user)
        except Carrito.DoesNotExist:
            raise serializers.ValidationError("El carrito de compras está vacío.")

        items_carrito = carrito.items.all()
        if not items_carrito.exists():
            raise serializers.ValidationError("No hay ítems en el carrito para procesar el pedido.")

        for item in items_carrito:
            if item.producto.stock < item.cantidad:
                raise serializers.ValidationError(f"Stock insuficiente para la prenda: {item.producto.nombre}")

        pedido = Pedido.objects.create(
            comprador=user,
            total=carrito.total,
            **validated_data
        )

        for item in items_carrito:
            ItemPedido.objects.create(
                pedido=pedido,
                producto=item.producto,
                nombre_producto=item.producto.nombre,
                precio_unitario=item.producto.precio,
                cantidad=item.cantidad
            )
            item.producto.stock -= item.cantidad
            item.producto.save()

        items_carrito.delete()

        return pedido