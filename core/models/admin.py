from django.contrib import admin
from .user import CustomUser
from .vendedor import PerfilVendedor

admin.site.register(CustomUser)
admin.site.register(PerfilVendedor)