"""
Módulo de serializers de usuario para la API.
Reexporta los serializadores de perfil de usuario de core.serializers.
"""
from core.serializers.userDetail import (
    UserDetailSerializer,
    UserMeSerializer,
    UsuarioSerializer,
)
from core.serializers.vendedor import (
    PerfilVendedorSerializer,
    SerVendedorSerializer,
)
from core.validators import (
    validar_alias_bancario,
    ALIAS_BANCARIO_ERROR_MESSAGE,
)

__all__ = [
    "UserDetailSerializer",
    "UserMeSerializer",
    "UsuarioSerializer",
    "PerfilVendedorSerializer",
    "SerVendedorSerializer",
    "validar_alias_bancario",
    "ALIAS_BANCARIO_ERROR_MESSAGE",
]

