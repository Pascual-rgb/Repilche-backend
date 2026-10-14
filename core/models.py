from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
  class Role(models.TextChoices):
    ADMIN = "ADMIN", "Administrador"
    SELLER = "SELLER", "Vendedor"
    BUYER = "BUYER", "Comprador"

  role = models.CharField(
      max_length=20, choices=Role.choices, default=Role.BUYER
  )
  email = models.EmailField(unique=True)

  # Si usas email como identificador principal en lugar de username:
  USERNAME_FIELD = "email"
  REQUIRED_FIELDS = ["username", "first_name", "last_name"]

  def __str__(self):
    return f"{self.email} ({self.role})"