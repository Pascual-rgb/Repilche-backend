from rest_framework import serializers
from django.contrib.auth import get_user_model
from .vendedor import PerfilVendedorSerializer

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="first_name", required=False)
    lastName = serializers.CharField(source="last_name", required=False)
    usuario = serializers.CharField(source="username", required=False, allow_null=True)
    numberPhone = serializers.CharField(source="phone", required=False, allow_blank=True)
    celphone = serializers.CharField(source="phone", required=False, allow_blank=True)
    perfil_vendedor = PerfilVendedorSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "name",
            "last_name",
            "lastName",
            "username",
            "usuario",
            "phone",
            "numberPhone",
            "celphone",
            "is_vendedor",
            "perfil_vendedor",
            "date_joined",
        ]
        read_only_fields = ["id", "is_vendedor", "date_joined"]