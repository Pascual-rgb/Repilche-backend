from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

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
            "is_staff": self.user.is_staff,
            "is_superuser": self.user.is_superuser,
            "role": "admin" if (self.user.is_staff or self.user.is_superuser) else "user",
            "es_admin": bool(self.user.is_staff or self.user.is_superuser),
        }
        return data