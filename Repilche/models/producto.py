from django.db import models
from core.models import CustomUser
from .categoria import Categoria


class Producto(models.Model):
    class Estado(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        PAUSADO = "PAUSADO", "Pausado"
        VENDIDO = "VENDIDO", "Vendido"

    class EstadoModeracion(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Rechazado"

    # Alias de compatibilidad
    EstadoProducto = Estado

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
    
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.DISPONIBLE,
        verbose_name="Estado de publicación",
    )
    estado_moderacion = models.CharField(
        max_length=20,
        choices=EstadoModeracion.choices,
        default=EstadoModeracion.PENDIENTE,
        verbose_name="Estado de moderación",
    )
    moderado_el = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de moderación")
    motivo_rechazo = models.TextField(blank=True, verbose_name="Motivo de rechazo")
    
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de publicación")
    actualizado_el = models.DateTimeField(auto_now=True, verbose_name="Última modificación")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["-creado_el"]

    def __str__(self):
        return f"{self.nombre} - ${self.precio} ({self.estado_moderacion})"