from core.models import User
from django.db import models


class Product(models.Model):
  seller = models.ForeignKey(
      User,
      on_delete=models.CASCADE,
      limit_choices_to={"role": User.Role.SELLER},
  )
  name = models.CharField(max_length=255)
  description = models.TextField()
  price = models.DecimalField(max_digits=10, decimal_places=2)
  stock = models.PositiveIntegerField()
  created_at = models.DateTimeField(auto_now_add=True)


class Order(models.Model):
  class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pendiente de pago"
    VERIFYING = "VERIFYING", "Comprobante enviado / En revisión"
    PAID = "PAID", "Pagado / Aprobado"
    CANCELLED = "CANCELLED", "Cancelado"

  buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
  status = models.CharField(
      max_length=20,
      choices=PaymentStatus.choices,
      default=PaymentStatus.PENDING,
  )
  total_amount = models.DecimalField(max_digits=10, decimal_places=2)
  receipt_image = models.ImageField(
      upload_to="receipts/", null=True, blank=True
  )  # Para subir la foto de la transferencia
  created_at = models.DateTimeField(auto_now_add=True)