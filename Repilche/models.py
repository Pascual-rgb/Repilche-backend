from django.conf import settings
from django.db import models
from core.models import CustomUser

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
# Carrito de Compras
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
# Pedido / Orden de Compra
# ==============================================================================
class Pedido(models.Model):
    """
    Orden de compra generada al finalizar el checkout.
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