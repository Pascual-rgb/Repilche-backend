from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,
    PerfilVendedor,
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