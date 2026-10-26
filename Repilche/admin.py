from django.contrib import admin
from .models import (Categoria, Producto, Carrito, ItemCarrito, Pedido, ItemPedido, Notificacion)


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "usuario", "tipo", "leida", "creado_el")
    list_filter = ("tipo", "leida", "creado_el")
    search_fields = ("titulo", "mensaje", "usuario__email")
    readonly_fields = ("creado_el",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug")
    prepopulated_fields = {"slug": ("nombre",)}
    search_fields = ("nombre",)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "vendedor", "categoria", "precio", "stock", "estado", "creado_el")
    list_filter = ("estado", "categoria", "creado_el")
    search_fields = ("nombre", "descripcion", "vendedor__email")
    readonly_fields = ("creado_el", "actualizado_el")

class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0
    readonly_fields = ("subtotal",)

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "total_items", "total", "actualizado_el")
    inlines = [ItemCarritoInline]
    search_fields = ("usuario__email", "usuario__first_name")

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    # El código secreto y el estado de entrega ahora viven en ItemPedido
    readonly_fields = ("nombre_producto", "precio_unitario", "subtotal", "codigo_secreto")
    fields = ("vendedor", "producto", "nombre_producto", "precio_unitario", "cantidad", "subtotal", "codigo_secreto", "estado_entrega")

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "comprador", "estado_pago", "total", "creado_el")
    list_filter = ("estado_pago", "creado_el")
    search_fields = ("comprador__email", "comprador__first_name")
    inlines = [ItemPedidoInline]
    readonly_fields = ("creado_el", "actualizado_el")

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "vendedor", "nombre_producto", "codigo_secreto", "estado_entrega")
    list_filter = ("estado_entrega",)
    search_fields = ("codigo_secreto", "nombre_producto", "vendedor__usuario__email")
    readonly_fields = ("codigo_secreto",)