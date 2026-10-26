from django.db import models
from core.models import CustomUser
from .categoria import Categoria


class Producto(models.Model):
    class EstadoProducto(models.TextChoices):
        REVISION = "revision", "En Revisión"
        APROBADO = "aprobado", "Aprobado"
        RECHAZADO = "rechazado", "Rechazado"
        VENDIDO = "vendido", "Vendido"

    vendedor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="productos",
        verbose_name="Vendedor",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="Categoría",
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la prenda")
    descripcion = models.TextField(verbose_name="Descripción de la prenda")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio ($)")
    stock = models.PositiveIntegerField(default=1, verbose_name="Stock disponible")
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True, verbose_name="Foto")
    
    # Nuevos estados de moderación y justificación
    estado = models.CharField(
        max_length=20,
        choices=EstadoProducto.choices,
        default=EstadoProducto.REVISION,
        verbose_name="Estado de moderación",
    )
    justificacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Justificación de rechazo",
        help_text="Motivo por el cual el administrador rechazó el producto",
    )
    
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de publicación")
    actualizado_el = models.DateTimeField(auto_now=True, verbose_name="Última modificación")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["-creado_el"]

    def __str__(self):
        return f"{self.nombre} - ${self.precio} ({self.get_estado_display()})"