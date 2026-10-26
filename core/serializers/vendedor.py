from rest_framework import serializers
from core.models import PerfilVendedor


class PerfilVendedorSerializer(serializers.ModelSerializer):
    locality = serializers.CharField(source="localidad", required=False)
    llegoHasta = serializers.CharField(source="llego_hasta", required=False)
    description = serializers.CharField(source="descripcion", required=False, allow_blank=True)

    class Meta:
        model = PerfilVendedor
        fields = [
            "id",
            "localidad",
            "locality",
            "llego_hasta",
            "llegoHasta",
            "cvu",
            "descripcion",
            "description",
            "creado_el",
        ]
        read_only_fields = ["id", "creado_el"]
        extra_kwargs = {
            "localidad": {"required": False},
            "llego_hasta": {"required": False},
            "cvu": {"required": False},
        }

    def validate(self, attrs):
        if not attrs.get("localidad") and not self.initial_data.get("locality"):
            raise serializers.ValidationError({"localidad": "La localidad es requerida."})
        if not attrs.get("llego_hasta") and not self.initial_data.get("llegoHasta"):
            raise serializers.ValidationError({"llego_hasta": "La zona de entrega es requerida."})
        if not attrs.get("cvu") and not self.initial_data.get("cvu"):
            raise serializers.ValidationError({"cvu": "El CVU / CBU es requerido."})
        return attrs