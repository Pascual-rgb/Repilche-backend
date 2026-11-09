from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from core.serializers.userDetail import UserDetailSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser
        token["role"] = "admin" if (user.is_staff or user.is_superuser) else "user"
        token["es_admin"] = bool(user.is_staff or user.is_superuser)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        access_token = data.get("access")
        refresh_token = data.get("refresh")

        # Serialización completa del perfil del usuario (incluye datos básicos, roles, perfil_vendedor y alias)
        user_data = UserDetailSerializer(self.user).data

        data["user"] = user_data
        data["access_token"] = access_token
        data["refresh_token"] = refresh_token
        data["tokens"] = {
            "access": access_token,
            "refresh": refresh_token,
        }
        return data