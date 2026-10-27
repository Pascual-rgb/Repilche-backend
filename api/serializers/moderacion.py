from rest_framework import serializers
from Repilche.models import Producto


class ModeracionProductoSerializer(serializers.ModelSerializer):
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
            "estado_moderacion",
            "motivo_rechazo",
            "moderado_el",
            "creado_el",
        ]
        read_only_fields = ["id", "vendedor", "creado_el", "moderado_el"]


class RechazarProductoSerializer(serializers.Serializer):
    motivo = serializers.CharField(required=True, allow_blank=False, help_text="Motivo de rechazo de la prenda")