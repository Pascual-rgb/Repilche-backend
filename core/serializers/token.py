from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

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
        }
        return data