from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models


# ==============================================================================
# Manager personalizado para CustomUser
# ==============================================================================
class CustomUserManager(BaseUserManager):
    """Manager que usa email como identificador único en lugar de username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_vendedor", False)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# ==============================================================================
# Modelo de Usuario Personalizado
# ==============================================================================
class CustomUser(AbstractUser):
    """
    Usuario personalizado de Repilche.
    Identificador principal: email (no username).
    El username es opcional — se puede completar desde Editar Perfil.
    """

    # Email como campo de login principal
    email = models.EmailField(
        unique=True,
        verbose_name="Correo electrónico",
        error_messages={
            "unique": "Ya existe una cuenta registrada con este correo."
        },
    )

    # Datos personales obligatorios al registro
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

    # Username opcional — se puede completar desde Editar Perfil
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Nombre de usuario",
        help_text="Opcional. Se puede definir o editar desde el perfil.",
    )

    # Rol simplificado: comprador por defecto, se activa con el form "Ser Vendedor"
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

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"


# ==============================================================================
# Perfil de Vendedor (se crea al completar el formulario "Ser Vendedor")
# ==============================================================================
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
        verbose_name="Localidad",
        help_text="Ciudad o barrio desde donde vende/entrega.",
    )
    llego_hasta = models.CharField(
        max_length=150,
        verbose_name="Llego hasta",
        help_text="Zona o límite de entrega del vendedor.",
    )
    cvu = models.CharField(
        max_length=100,
        verbose_name="CVU / CBU",
        help_text="Alias o número de cuenta para recibir pagos.",
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción del perfil de vendedor",
    )
    creado_el = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de alta como vendedor",
    )

    class Meta:
        verbose_name = "Perfil de Vendedor"
        verbose_name_plural = "Perfiles de Vendedor"

    def __str__(self):
        return f"Vendedor: {self.usuario.get_full_name()} ({self.localidad})"


# ==============================================================================
# Categoría de Prendas
# ==============================================================================
class Categoria(models.Model):
    """Categoría para clasificación de prendas en el catálogo."""

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de categoría",
        help_text="Ej: Remeras, Pantalones, Calzado, Accesorios, Abrigo",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name="Slug (identificador URL)",
    )

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


# ==============================================================================
# Producto / Prenda de Ropa
# ==============================================================================
class Producto(models.Model):
    """
    Prenda o producto publicado por un vendedor en Repilche.
    Estructurado para satisfacer los campos esperados por el frontend:
    id, name, descrp, img, stock, cat, precio, vendedor.
    """

    class EstadoProducto(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        PAUSADO = "PAUSADO", "Pausado"
        VENDIDO = "VENDIDO", "Vendido"

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
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre de la prenda",
        help_text="name en el frontend",
    )
    descripcion = models.TextField(
        verbose_name="Descripción de la prenda",
        help_text="descrp / description en el frontend",
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio ($)",
        help_text="precio en el frontend",
    )
    stock = models.PositiveIntegerField(
        default=1,
        verbose_name="Stock disponible",
        help_text="stock en el frontend",
    )
    imagen = models.ImageField(
        upload_to="productos/",
        blank=True,
        null=True,
        verbose_name="Foto de la prenda",
        help_text="img en el frontend",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoProducto.choices,
        default=EstadoProducto.DISPONIBLE,
        verbose_name="Estado de publicación",
    )
    creado_el = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de publicación",
    )
    actualizado_el = models.DateTimeField(
        auto_now=True,
        verbose_name="Última modificación",
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["-creado_el"]

    def __str__(self):
        return f"{self.nombre} - ${self.precio} ({self.vendedor.get_full_name()})"