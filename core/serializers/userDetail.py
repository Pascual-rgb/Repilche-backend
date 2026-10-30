from rest_framework import serializers
from django.contrib.auth import get_user_model
from .vendedor import PerfilVendedorSerializer

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="first_name", required=False)
    nombre = serializers.CharField(source="first_name", required=False)
    lastName = serializers.CharField(source="last_name", required=False)
    apellido = serializers.CharField(source="last_name", required=False)
    usuario = serializers.CharField(source="username", required=False, allow_null=True)
    numberPhone = serializers.CharField(source="phone", required=False, allow_blank=True)
    celphone = serializers.CharField(source="phone", required=False, allow_blank=True)
    telefono = serializers.CharField(source="phone", required=False, allow_blank=True)
    perfil_vendedor = PerfilVendedorSerializer(read_only=True)
    role = serializers.SerializerMethodField()
    es_admin = serializers.SerializerMethodField()

    def get_role(self, obj):
        return "admin" if (obj.is_staff or obj.is_superuser) else "user"

    def get_es_admin(self, obj):
        return bool(obj.is_staff or obj.is_superuser)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "name",
            "nombre",
            "last_name",
            "lastName",
            "apellido",
            "username",
            "usuario",
            "phone",
            "numberPhone",
            "celphone",
            "telefono",
            "is_vendedor",
            "perfil_vendedor",
            "date_joined",
            "is_staff",
            "is_superuser",
            "role",
            "es_admin",
        ]
        read_only_fields = [
            "id",
            "is_vendedor",
            "date_joined",
            "is_staff",
            "is_superuser",
            "role",
            "es_admin",
        ]