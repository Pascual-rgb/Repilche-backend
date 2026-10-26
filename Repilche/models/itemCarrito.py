from django.db import models
from .carrito import Carrito
from .producto import Producto


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Carrito",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="en_carritos",
        verbose_name="Prenda / Producto",
    )
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Agregado el")

    class Meta:
        verbose_name = "Ítem de Carrito"
        verbose_name_plural = "Ítems de Carrito"
        unique_together = ("carrito", "producto")

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"