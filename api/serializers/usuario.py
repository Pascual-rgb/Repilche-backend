"""
Módulo de serializers de usuario para la API.
Reexporta los serializadores de perfil de usuario de core.serializers.
"""
from core.serializers.userDetail import (
    UserDetailSerializer,
    UserMeSerializer,
    UsuarioSerializer,
)

__all__ = [
    "UserDetailSerializer",
    "UserMeSerializer",
    "UsuarioSerializer",
]

