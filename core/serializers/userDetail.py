import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.models import PerfilVendedor
from core.validators import validar_alias_bancario, ALIAS_BANCARIO_ERROR_MESSAGE
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
    alias_bancario = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=False,
        help_text="Alias bancario único para cobro de ventas (exclusivo para vendedores).",
    )
    alias = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=False,
        help_text="Alias alternativo para alias_bancario.",
    )
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
            "alias_bancario",
            "alias",
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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        is_vendedor = bool(
            getattr(instance, "is_vendedor", False)
            or hasattr(instance, "perfil_vendedor")
            or PerfilVendedor.objects.filter(usuario=instance).exists()
        )
        
        if is_vendedor:
            perfil = getattr(instance, "perfil_vendedor", None)
            if not perfil:
                perfil = PerfilVendedor.objects.filter(usuario=instance).first()
            alias_val = getattr(perfil, "cvu", None) or getattr(perfil, "alias_bancario", "")
            data["alias_bancario"] = alias_val
            data["alias"] = alias_val
        else:
            data["alias_bancario"] = None
            data["alias"] = None

        return data

    def validate(self, attrs):
        alias_val = None
        has_alias = False

        if "alias_bancario" in attrs:
            alias_val = attrs.get("alias_bancario")
            has_alias = True
        elif "alias" in attrs:
            alias_val = attrs.get("alias")
            has_alias = True
        elif hasattr(self, "initial_data"):
            if "alias_bancario" in self.initial_data:
                alias_val = self.initial_data.get("alias_bancario")
                has_alias = True
            elif "alias" in self.initial_data:
                alias_val = self.initial_data.get("alias")
                has_alias = True

        if has_alias:
            user = self.instance or (self.context.get("request").user if "request" in self.context else None)
            is_vendedor = bool(
                user and (
                    getattr(user, "is_vendedor", False)
                    or hasattr(user, "perfil_vendedor")
                    or PerfilVendedor.objects.filter(usuario=user).exists()
                )
            )
            if not is_vendedor:
                raise serializers.ValidationError(
                    {"alias_bancario": "Solo los usuarios vendedores pueden configurar o editar un alias bancario."}
                )

            if alias_val is None or str(alias_val).strip() == "":
                raise serializers.ValidationError(
                    {"alias_bancario": ALIAS_BANCARIO_ERROR_MESSAGE, "alias": ALIAS_BANCARIO_ERROR_MESSAGE}
                )

            try:
                alias_normalizado = validar_alias_bancario(str(alias_val))
            except serializers.ValidationError as err:
                msg = err.detail if hasattr(err, "detail") else str(err)
                raise serializers.ValidationError({"alias_bancario": msg, "alias": msg})

            attrs["alias_bancario"] = alias_normalizado
            attrs["alias"] = alias_normalizado

        return super().validate(attrs)

    def update(self, instance, validated_data):
        alias_bancario = validated_data.pop("alias_bancario", None)
        alias = validated_data.pop("alias", None)
        alias_to_update = alias_bancario if alias_bancario is not None else alias

        instance = super().update(instance, validated_data)

        if alias_to_update is not None:
            alias_clean = str(alias_to_update).strip().lower()
            perfil, _ = PerfilVendedor.objects.update_or_create(
                usuario=instance,
                defaults={"cvu": alias_clean},
            )
            instance.perfil_vendedor = perfil

        return instance


# Aliases de compatibilidad
UserMeSerializer = UserDetailSerializer
UsuarioSerializer = UserDetailSerializer
