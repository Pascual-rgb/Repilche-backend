from django.db import models
from core.models import CustomUser


class Notificacion(models.Model):
    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="notificaciones",
        verbose_name="Usuario Destinatario",
    )
    tipo = models.CharField(
        max_length=30,
        default="SISTEMA",
        verbose_name="Tipo de Notificación",
    )
    titulo = models.CharField(max_length=255, verbose_name="Título")
    mensaje = models.TextField(verbose_name="Mensaje")
    leida = models.BooleanField(default=False, verbose_name="¿Leída?")
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-creado_el"]

    def __str__(self):
        return f"[{self.tipo}] {self.titulo} - {self.usuario.email}"