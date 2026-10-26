from django.db import models
from core.models import CustomUser


class Notificacion(models.Model):
    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="notificaciones",
        verbose_name="Usuario Destinatario",
    )
    titulo = models.CharField(max_length=255, verbose_name="Título")
    mensaje = models.TextField(verbose_name="Mensaje")
    leido = models.BooleanField(default=False, verbose_name="¿Leído?")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-fecha"]

    def __str__(self):
        return f"[{'Leída' if self.leido else 'Nueva'}] {self.titulo} - {self.usuario.email}"