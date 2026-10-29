from rest_framework import serializers
from Repilche.models import Producto


class ModeracionProductoSerializer(serializers.ModelSerializer):
    imagen_url = serializers.CharField(source='imagen', read_only=True)
    img = serializers.CharField(source='imagen', read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id",
            "vendedor",
            "categoria",
            "nombre",
            "descripcion",
            "precio",
            "stock",
            "imagen",
            "imagen_url",
            "img",
            "estado_moderacion",
            "motivo_rechazo",
            "moderado_el",
            "creado_el",
        ]
        read_only_fields = ["id", "vendedor", "creado_el", "moderado_el"]


class RechazarProductoSerializer(serializers.Serializer):
    motivo = serializers.CharField(required=True, allow_blank=False, help_text="Motivo de rechazo de la prenda")