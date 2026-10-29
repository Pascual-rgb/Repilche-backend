from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager que usa email como identificador único en lugar de username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        email = self.normalize_email(email)
        extra_fields.setdefault("username", None)
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_vendedor", False)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Usuario personalizado de Repilche.
    Identificador principal: email (no username).
    """

    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Nombre de usuario",
        help_text="Opcional. Se puede definir o editar desde el perfil.",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Correo electrónico",
        error_messages={
            "unique": "Ya existe una cuenta registrada con este correo."
        },
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name="Nombre",
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name="Apellido",
    )
    phone = models.CharField(
        max_length=25,
        verbose_name="Teléfono / Celular",
        blank=True,
        default="",
    )
    is_vendedor = models.BooleanField(
        default=False,
        verbose_name="¿Es vendedor?",
        help_text="Se activa cuando el usuario completa el formulario 'Ser vendedor'.",
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def pedidos(self):
        return getattr(self, "compras", None)

    @property
    def items_vendidos(self):
        return getattr(self, "ventas_items", None)

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"