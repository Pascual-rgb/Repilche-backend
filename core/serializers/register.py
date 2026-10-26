from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
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
        name = attrs.pop("name", None) or attrs.get("first_name")
        if not name or not str(name).strip():
            raise serializers.ValidationError({"name": "El nombre es obligatorio."})
        attrs["first_name"] = str(name).strip()

        last_name = attrs.pop("lastName", None) or attrs.get("last_name")
        if not last_name or not str(last_name).strip():
            raise serializers.ValidationError({"lastName": "El apellido es obligatorio."})
        attrs["last_name"] = str(last_name).strip()

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