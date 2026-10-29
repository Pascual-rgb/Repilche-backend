import string
import random
from django.conf import settings
from django.db import models
from .pedido import Pedido
from .producto import Producto


def generar_codigo_secreto():
    return ''.join(random.choices(string.digits, k=6))


class ItemPedido(models.Model):
    class EstadoEntrega(models.TextChoices):
        EN_CUSTODIA = "en_custodia", "En Custodia"
        ENTREGADO = "entregado", "Entregado"
        CANCELADO = "cancelado", "Cancelado"

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Pedido",
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ventas_items",
        verbose_name="Vendedor",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="en_pedidos",
        verbose_name="Prenda original",
    )
    nombre_producto = models.CharField(max_length=200, blank=True, verbose_name="Nombre histórico")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio unitario")
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    
    # Código secreto de 6 dígitos y estados de entrega exigidos
    codigo_secreto = models.CharField(
        max_length=6,
        default=generar_codigo_secreto,
        editable=False,
        verbose_name="Código Secreto (6 dígitos)",
    )
    estado_entrega = models.CharField(
        max_length=20,
        choices=EstadoEntrega.choices,
        default=EstadoEntrega.EN_CUSTODIA,
        verbose_name="Estado de entrega",
    )
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Ítem de Pedido"
        verbose_name_plural = "Ítems de Pedido"

    @property
    def precio(self):
        return self.precio_unitario

    @precio.setter
    def precio(self, value):
        self.precio_unitario = value

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def save(self, *args, **kwargs):
        if self.producto and not self.nombre_producto:
            self.nombre_producto = self.producto.nombre
        if self.producto and not self.precio_unitario:
            self.precio_unitario = self.producto.precio
        if self.producto and not self.vendedor and hasattr(self.producto, 'vendedor'):
            self.vendedor = self.producto.vendedor
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Item {self.nombre_producto} [{self.estado_entrega}] - Código: {self.codigo_secreto}"