from django.conf import settings
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

# ==============================================================================
# Carrito de Compras (Tarea 04)
# ==============================================================================
class Carrito(models.Model):
    """
    Carrito de compras vinculado al usuario autenticado.
    """

    usuario = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="carrito",
        verbose_name="Usuario",
    )
    creado_el = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    actualizado_el = models.DateTimeField(
        auto_now=True,
        verbose_name="Última modificación",
    )

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

class ItemCarrito(models.Model):
    """
    Elemento individual dentro del carrito de compras.
    """

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
    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name="Cantidad",
    )
    creado_el = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Agregado el",
    )

    class Meta:
        verbose_name = "Ítem de Carrito"
        verbose_name_plural = "Ítems de Carrito"
        unique_together = ("carrito", "producto")

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"

# ==============================================================================
# Pedido / Orden de Compra (Tarea 04)
# ==============================================================================
class Pedido(models.Model):
    """
    Orden de compra generada al finalizar el checkout.
    Contiene:
    - Código Secreto de 6 dígitos para validar la entrega.
    - Estado del pago bancario.
    - Alias oficial de Repilche utilizado.
    - Comprobante adjunto.
    """

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
    codigo_secreto = models.CharField(
        max_length=6,
        unique=True,
        blank=True,
        verbose_name="Código Secreto (6 dígitos)",
        help_text="Código único de 6 dígitos numéricos para verificar la entrega",
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
        help_text="Alias bancario oficial utilizado para la transferencia",
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
        help_text="Captura o foto del comprobante de transferencia bancaria",
    )
    creado_el = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha del pedido",
    )
    actualizado_el = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-creado_el"]

    def save(self, *args, **kwargs):
        if not self.codigo_secreto:
            import secrets
            import string

            # Generar código secreto único de 6 dígitos numéricos
            while True:
                codigo = "".join(secrets.choice(string.digits) for _ in range(6))
                if not Pedido.objects.filter(codigo_secreto=codigo).exists():
                    self.codigo_secreto = codigo
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido #{self.id} - {self.comprador.get_full_name()} (${self.total}) [Código: {self.codigo_secreto}]"

class ItemPedido(models.Model):
    """
    Línea individual de detalle del pedido.
    Guarda el precio unitario histórico congelado al momento de comprar
    y el nombre de la prenda en caso de que el producto sea modificado o eliminado.
    """

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Pedido",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="en_pedidos",
        verbose_name="Prenda / Producto original",
        help_text="Si el producto se borra del catálogo, el registro contable persiste",
    )
    nombre_producto = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nombre histórico de la prenda",
        help_text="Guarda el nombre de la prenda congelado al momento de comprar",
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio Unitario Histórico ($)",
        help_text="Precio congelado al momento de la compra",
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name="Cantidad",
    )

    class Meta:
        verbose_name = "Ítem de Pedido"
        verbose_name_plural = "Ítems de Pedido"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def save(self, *args, **kwargs):
        if self.producto and not self.nombre_producto:
            self.nombre_producto = self.producto.nombre
        if self.producto and not self.precio_unitario:
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad}x {self.nombre_producto} (${self.precio_unitario})"