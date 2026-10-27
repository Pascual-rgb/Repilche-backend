from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    class Tipo(models.TextChoices):
        INFO = "INFO", "Información"
        MODERACION = "MODERACION", "Moderación"
        PEDIDO = "PEDIDO", "Pedido"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones",
        verbose_name="Usuario",
    )
    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.INFO,
        verbose_name="Tipo",
    )
    titulo = models.CharField(max_length=150, verbose_name="Título")
    mensaje = models.TextField(verbose_name="Mensaje")
    leida = models.BooleanField(default=False, verbose_name="Leída")
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-creado_el"]
        indexes = [models.Index(fields=["usuario", "leida"], name="ix_notif_usuario_leida")]

    def __str__(self):
        return f"[{'Leída' if self.leida else 'Nueva'}] {self.titulo} - {self.usuario}"
