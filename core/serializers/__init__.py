from .register import RegisterSerializer
from .userDetail import UserDetailSerializer, UserMeSerializer, UsuarioSerializer
from .token import CustomTokenObtainPairSerializer
from .vendedor import PerfilVendedorSerializer

__all__ = [
    "RegisterSerializer",
    "UserDetailSerializer",
    "UserMeSerializer",
    "UsuarioSerializer",
    "CustomTokenObtainPairSerializer",
    "PerfilVendedorSerializer",
]