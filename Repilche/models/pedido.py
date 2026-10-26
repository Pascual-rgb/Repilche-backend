from django.conf import settings
from django.db import models
from core.models import CustomUser


class Pedido(models.Model):
    class EstadoPago(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente de verificación"
        PAGADO = "PAGADO", "Pagado y confirmado"
        CANCELADO = "CANCELADO", "Cancelado / Rechazado"

    comprador = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="pedidos",
        verbose_name="Comprador",
    )
    estado_pago = models.CharField(
        max_length=20,
        choices=EstadoPago.choices,
        default=EstadoPago.PENDIENTE,
        verbose_name="Estado del pago",
    )
    alias_pago = models.CharField(
        max_length=100,
        default=getattr(settings, "REPILCHE_ALIAS_PAGO", "REPILCHE.OFICIAL.TRELEW"),
        verbose_name="Alias de Repilche para el pago",
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total del pedido ($)",
    )
    comprobante = models.ImageField(
        upload_to="comprobantes/",
        blank=True,
        null=True,
        verbose_name="Comprobante de transferencia",
    )
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del pedido")
    actualizado_el = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-creado_el"]

    def __str__(self):
        return f"Pedido #{self.id} - {self.comprador.get_full_name()} (${self.total})"