from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Categoria,
    CustomUser,
    PerfilVendedor,
    Producto,
    Carrito,
    ItemCarrito,
    Pedido,
    ItemPedido,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Panel de administración para el usuario personalizado de Repilche."""

    # Campos al EDITAR un usuario existente
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Datos Personales",
            {"fields": ("first_name", "last_name", "username", "phone")},
        ),
        (
            "Rol en Repilche",
            {"fields": ("is_vendedor",)},
        ),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )

    # Campos al CREAR un usuario nuevo
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "phone",
                    "password1",
                    "password2",
                    "is_vendedor",
                ),
            },
        ),
    )

    list_display = (
        "email",
        "first_name",
        "last_name",
        "phone",
        "is_vendedor",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_vendedor", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name", "username", "phone")
    ordering = ("email",)


@admin.register(PerfilVendedor)
class PerfilVendedorAdmin(admin.ModelAdmin):
    """Panel de administración para los perfiles de vendedor."""

    list_display = ("usuario", "localidad", "llego_hasta", "cvu", "creado_el")
    search_fields = (
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",
        "localidad",
    )
    readonly_fields = ("creado_el",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Panel de administración para Categorías de prendas."""

    list_display = ("nombre", "slug", "total_productos")
    search_fields = ("nombre", "slug")
    prepopulated_fields = {"slug": ("nombre",)}

    def total_productos(self, obj):
        return obj.productos.count()

    total_productos.short_description = "Productos activos"


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Panel de administración para Productos / Prendas."""

    list_display = (
        "nombre",
        "categoria",
        "precio",
        "stock",
        "vendedor",
        "estado",
        "creado_el",
    )
    list_filter = ("categoria", "estado", "creado_el")
    search_fields = (
        "nombre",
        "descripcion",
        "vendedor__email",
        "vendedor__first_name",
        "vendedor__last_name",
    )
    list_editable = ("precio", "stock", "estado")
    readonly_fields = ("creado_el", "actualizado_el")
    autocomplete_fields = ("vendedor", "categoria")


class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0
    autocomplete_fields = ("producto",)


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    """Panel de administración para Carritos de compras."""

    list_display = ("usuario", "total_items_display", "total_display", "actualizado_el")
    search_fields = ("usuario__email", "usuario__first_name", "usuario__last_name")
    readonly_fields = ("creado_el", "actualizado_el")
    inlines = [ItemCarritoInline]

    def total_items_display(self, obj):
        return obj.total_items

    total_items_display.short_description = "Cant. Prendas"

    def total_display(self, obj):
        return f"${obj.total}"

    total_display.short_description = "Total acumulado"


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ("subtotal",)
    autocomplete_fields = ("producto",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    """Panel de administración para Pedidos / Órdenes de Compra."""

    list_display = (
        "id",
        "codigo_secreto",
        "comprador",
        "total",
        "estado_pago",
        "alias_pago",
        "creado_el",
    )
    list_filter = ("estado_pago", "creado_el")
    search_fields = (
        "codigo_secreto",
        "comprador__email",
        "comprador__first_name",
        "comprador__last_name",
        "alias_pago",
    )
    list_editable = ("estado_pago",)
    readonly_fields = ("codigo_secreto", "creado_el", "actualizado_el")
    inlines = [ItemPedidoInline]


