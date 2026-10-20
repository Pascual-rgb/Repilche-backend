from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from core.models import PerfilVendedor
from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserDetailSerializer,
    PerfilVendedorSerializer,
)

User = get_user_model()


# ==============================================================================
# 1. Registro de Usuario (/api/registro/ o /api/auth/register/)
# ==============================================================================
class RegistroView(generics.CreateAPIView):
    """
    Endpoint para registrar un nuevo usuario en Repilche.
    Devuelve los datos del usuario creado y los tokens JWT (access y refresh)
    para permitir inicio de sesión automático.
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generar tokens JWT inmediatos
        refresh = RefreshToken.for_user(user)

        response_data = {
            "mensaje": "Usuario registrado exitosamente.",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "name": user.first_name,
                "lastName": user.last_name,
                "phone": user.phone,
                "numberPhone": user.phone,
                "celphone": user.phone,
                "username": user.username,
                "is_vendedor": user.is_vendedor,
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


# ==============================================================================
# 2. Login con JWT (/api/login/ o /api/auth/login/)
# ==============================================================================
class LoginView(TokenObtainPairView):
    """
    Endpoint de login con email y password.
    Devuelve 'access', 'refresh' y los datos completos del 'user'.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


# ==============================================================================
# 3. Perfil de Usuario Actual (/api/usuario/me/ o /api/me/)
# ==============================================================================
class UsuarioMeView(generics.RetrieveUpdateAPIView):
    """
    GET: Devuelve los datos del usuario autenticado y su perfil de vendedor (si tiene).
    PATCH/PUT: Permite actualizar datos del perfil (nombre, apellido, username, teléfono, email).
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ==============================================================================
# 4. Convertirse en Vendedor (/api/vendedor/ o /api/ser-vendedor/)
# ==============================================================================
class SerVendedorView(APIView):
    """
    Endpoint para completar el formulario /ser-vendedor.
    Crea o actualiza el PerfilVendedor y activa is_vendedor=True en el usuario.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Extraer campos soportando tanto camelCase del form como snake_case
        data = {
            "localidad": request.data.get("locality") or request.data.get("localidad"),
            "llego_hasta": request.data.get("llegoHasta") or request.data.get("llego_hasta"),
            "cvu": request.data.get("cvu"),
            "descripcion": request.data.get("description") or request.data.get("descripcion", ""),
        }

        # Si ya tiene un perfil existente, actualizarlo; si no, crearlo
        perfil, created = PerfilVendedor.objects.get_or_create(usuario=user, defaults=data)
        if not created:
            for key, value in data.items():
                if value is not None:
                    setattr(perfil, key, value)
            perfil.save()

        # Activar el rol de vendedor en el usuario
        if not user.is_vendedor:
            user.is_vendedor = True
            user.save(update_fields=["is_vendedor"])

        serializer = PerfilVendedorSerializer(perfil)
        return Response(
            {
                "mensaje": "¡Felicitaciones! Ahora sos vendedor en Repilche.",
                "perfil_vendedor": serializer.data,
                "is_vendedor": True,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
