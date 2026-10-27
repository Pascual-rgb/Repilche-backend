from django.db import models
from .user import CustomUser


class PerfilVendedor(models.Model):
    """
    Información adicional del vendedor.
    Se crea cuando el usuario completa el formulario /ser-vendedor.
    """

    usuario = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="perfil_vendedor",
        verbose_name="Usuario",
    )
    localidad = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Localidad",
        help_text="Ciudad o barrio desde vende/entrega.",
    )
    llego_hasta = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Llego hasta",
        help_text="Zona o límite de entrega del vendedor.",
    )
    cvu = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="CVU / CBU",
        help_text="Alias o número de cuenta para recibir pagos.",
    )
    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name="Descripción del perfil de vendedor",
    )
    creado_el = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de alta como vendedor",
    )

    class Meta:
        verbose_name = "Perfil de Vendedor"
        verbose_name_plural = "Perfiles de Vendedor"

    @property
    def alias_bancario(self):
        return self.cvu

    @alias_bancario.setter
    def alias_bancario(self, value):
        self.cvu = value

    @property
    def alias(self):
        return self.cvu

    @alias.setter
    def alias(self, value):
        self.cvu = value

    def __str__(self):
        return f"Vendedor: {self.usuario.get_full_name()} ({self.localidad})"