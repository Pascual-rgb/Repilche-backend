from rest_framework import serializers
from django.db import transaction
from Repilche.models import (Categoria, Producto, Carrito, ItemCarrito, Pedido, ItemPedido)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nombre", "slug"]


class ProductSerializer(serializers.ModelSerializer):
    categoria_detail = CategorySerializer(source='categoria', read_only=True)
    
    # Aliases de lectura para el frontend
    name = serializers.CharField(source='nombre', read_only=True)
    description = serializers.CharField(source='descripcion', read_only=True)
    price = serializers.DecimalField(source='precio', max_digits=10, decimal_places=2, read_only=True)
    img = serializers.ImageField(source='imagen', read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id",
            "vendedor",
            "categoria",
            "categoria_detail",
            "nombre",
            "name",
            "descripcion",
            "description",
            "precio",
            "price",
            "stock",
            "imagen",
            "img",
            "estado",
            "creado_el",
        ]
        read_only_fields = ["id", "vendedor", "creado_el"]

    def validate(self, attrs):
        # Validar que solo los usuarios con perfil de vendedor puedan crear productos
        user = self.context['request'].user
        if not user.is_authenticated or not user.is_vendedor:
            raise serializers.ValidationError("Debe ser un usuario vendedor registrado para publicar prendas.")
        return attrs

    def create(self, validated_data):
        # Asignar automáticamente el usuario autenticado como vendedor del producto
        validated_data['vendedor'] = self.context['request'].user
        return super().create(validated_data)


# ==============================================================================
# Serializadores de Carrito
# ==============================================================================
class ItemCarritoSerializer(serializers.ModelSerializer):
    producto_detail = ProductSerializer(source='producto', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemCarrito
        fields = ["id", "producto", "producto_detail", "cantidad", "subtotal"]


class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Carrito
        fields = ["id", "usuario", "items", "total", "total_items", "actualizado_el"]
        read_only_fields = ["id", "usuario"]


# ==============================================================================
# Serializadores de Pedidos / Checkout
# ==============================================================================
class ItemPedidoSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPedido
        fields = ["id", "producto", "nombre_producto", "precio_unitario", "cantidad", "subtotal"]
        read_only_fields = ["id", "nombre_producto", "precio_unitario"]


class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, read_only=True)
    comprobante = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "comprador",
            "codigo_secreto",
            "estado_pago",
            "alias_pago",
            "total",
            "comprobante",
            "items",
            "creado_el",
        ]
        read_only_fields = ["id", "comprador", "codigo_secreto", "estado_pago", "total", "creado_el"]

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

        # Validar stock antes de generar la orden
        for item in items_carrito:
            if item.producto.stock < item.cantidad:
                raise serializers.ValidationError(f"Stock insuficiente para la prenda: {item.producto.nombre}")

        # Crear el pedido
        pedido = Pedido.objects.create(
            comprador=user,
            total=carrito.total,
            **validated_data
        )

        # Crear ítems del pedido, congelar precios y descontar stock
        for item in items_carrito:
            ItemPedido.objects.create(
                pedido=pedido,
                producto=item.producto,
                nombre_producto=item.producto.nombre,
                precio_unitario=item.producto.precio,
                cantidad=item.cantidad
            )
            # Descontar stock
            item.producto.stock -= item.cantidad
            item.producto.save()

        # Vaciar el carrito tras generar la compra exitosamente
        items_carrito.delete()

        return pedido