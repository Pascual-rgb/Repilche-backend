from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from core.models import PerfilVendedor

User = get_user_model()


# ==============================================================================
# Serializador de Perfil de Vendedor
# ==============================================================================
class PerfilVendedorSerializer(serializers.ModelSerializer):
    # Soporta tanto nombres en español como los nombres usados en SerVendedorForm.tsx
    locality = serializers.CharField(source="localidad", required=False)
    llegoHasta = serializers.CharField(source="llego_hasta", required=False)
    description = serializers.CharField(source="descripcion", required=False, allow_blank=True)

    class Meta:
        model = PerfilVendedor
        fields = [
            "id",
            "localidad",
            "locality",
            "llego_hasta",
            "llegoHasta",
            "cvu",
            "descripcion",
            "description",
            "creado_el",
        ]
        read_only_fields = ["id", "creado_el"]
        extra_kwargs = {
            "localidad": {"required": False},
            "llego_hasta": {"required": False},
            "cvu": {"required": False},
        }

    def validate(self, attrs):
        # Asegurar que localidad y llego_hasta se completen con el source adecuado
        if not attrs.get("localidad") and not self.initial_data.get("locality"):
            raise serializers.ValidationError({"localidad": "La localidad es requerida."})
        if not attrs.get("llego_hasta") and not self.initial_data.get("llegoHasta"):
            raise serializers.ValidationError({"llego_hasta": "La zona de entrega es requerida."})
        if not attrs.get("cvu") and not self.initial_data.get("cvu"):
            raise serializers.ValidationError({"cvu": "El CVU / CBU es requerido."})
        return attrs


# ==============================================================================
# Serializador de Detalle y Edición de Usuario (Perfil)
# ==============================================================================
class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializador para ver y editar datos de perfil (/api/usuario/me/).
    Soporta aliases del frontend como 'name', 'lastName', 'usuario', 'numberPhone'.
    """
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


# ==============================================================================
# Serializador de Registro de Usuario
# ==============================================================================
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializador para registro de nuevos usuarios (/api/registro/).
    Acepta tanto nombres de Django (first_name, last_name, phone)
    como los nombres de los inputs de RegistroForm.tsx (name, lastName, numberPhone).
    """
    name = serializers.CharField(write_only=True, required=False)
    lastName = serializers.CharField(write_only=True, required=False)
    numberPhone = serializers.CharField(write_only=True, required=False)
    celphone = serializers.CharField(write_only=True, required=False)
    phone = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "name",
            "last_name",
            "lastName",
            "phone",
            "celphone",
            "numberPhone",
            "username",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "phone": {"required": False},
            "username": {"required": False},
        }

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        # 1. Mapear name -> first_name (obligatorio)
        name = attrs.pop("name", None) or attrs.get("first_name")
        if not name or not str(name).strip():
            raise serializers.ValidationError({"name": "El nombre es obligatorio."})
        attrs["first_name"] = str(name).strip()

        # 2. Mapear lastName -> last_name (obligatorio)
        last_name = attrs.pop("lastName", None) or attrs.get("last_name")
        if not last_name or not str(last_name).strip():
            raise serializers.ValidationError({"lastName": "El apellido es obligatorio."})
        attrs["last_name"] = str(last_name).strip()

        # 3. Mapear phone / celphone / numberPhone (OBLIGATORIO)
        raw_phone = (
            attrs.pop("numberPhone", None)
            or attrs.pop("celphone", None)
            or attrs.pop("phone", None)
            or attrs.get("phone")
        )
        if not raw_phone or not str(raw_phone).strip():
            raise serializers.ValidationError({
                "numberPhone": "El número de teléfono o celular es obligatorio."
            })
        attrs["phone"] = str(raw_phone).strip()

        return attrs


    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


# ==============================================================================
# Serializador de Login JWT Personalizado
# ==============================================================================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extiende SimpleJWT para autenticar por email y devolver datos del usuario en la respuesta.
    """
    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        data = super().validate(attrs)

        # Agregar datos útiles para la sesión del frontend
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "name": self.user.first_name,
            "lastName": self.user.last_name,
            "username": self.user.username,
            "phone": self.user.phone,
            "numberPhone": self.user.phone,
            "celphone": self.user.phone,
            "is_vendedor": self.user.is_vendedor,
        }
        return data
