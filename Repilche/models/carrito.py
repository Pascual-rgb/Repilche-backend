from django.db import models
from core.models import CustomUser


class Carrito(models.Model):
    usuario = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="carrito",
        verbose_name="Usuario",
    )
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    actualizado_el = models.DateTimeField(auto_now=True, verbose_name="Última modificación")

    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.cantidad for item in self.items.all())

    def __str__(self):
        return f"Carrito de {self.usuario.get_full_name()}"