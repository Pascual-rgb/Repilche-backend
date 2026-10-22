from django.contrib import admin
from .models import (Categoria, Producto, Carrito, ItemCarrito, Pedido, ItemPedido)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug")
    prepopulated_fields = {"slug": ("nombre",)}
    search_fields = ("nombre",)

class ItemProductoInline(admin.TabularInline):
    model = Producto
    extra = 0
    readonly_fields = ("creado_el",)

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
    readonly_fields = ("nombre_producto", "precio_unitario", "subtotal")

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "comprador", "codigo_secreto", "estado_pago", "total", "creado_el")
    list_filter = ("estado_pago", "creado_el")
    search_fields = ("codigo_secreto", "comprador__email", "comprador__first_name")
    inlines = [ItemPedidoInline]
    readonly_fields = ("codigo_secreto", "creado_el", "actualizado_el")