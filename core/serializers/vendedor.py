from rest_framework import serializers
from core.models import PerfilVendedor


class PerfilVendedorSerializer(serializers.ModelSerializer):
    locality = serializers.CharField(source="localidad", required=False)
    llegoHasta = serializers.CharField(source="llego_hasta", required=False)
    description = serializers.CharField(source="descripcion", required=False, allow_blank=True)
    alias_bancario = serializers.CharField(source="cvu", required=False)
    alias = serializers.CharField(source="cvu", required=False)

    class Meta:
        model = PerfilVendedor
        fields = [
            "id",
            "localidad",
            "locality",
            "llego_hasta",
            "llegoHasta",
            "cvu",
            "alias_bancario",
            "alias",
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

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = data.copy()
            # Si llegoHasta o llego_hasta viene como lista desde el frontend, lo unimos con comas
            llego = data.get("llegoHasta") or data.get("llego_hasta")
            if isinstance(llego, (list, tuple)):
                unido = ", ".join(str(c).strip() for c in llego if str(c).strip())
                data["llegoHasta"] = unido
                data["llego_hasta"] = unido
        return super().to_internal_value(data)

    def validate(self, attrs):
        localidad = attrs.get("localidad") or self.initial_data.get("locality")
        if not localidad or not str(localidad).strip():
            raise serializers.ValidationError({"localidad": "La localidad es requerida."})
        attrs["localidad"] = str(localidad).strip()

        llego_hasta_raw = attrs.get("llego_hasta") or self.initial_data.get("llegoHasta")
        if not llego_hasta_raw:
            raise serializers.ValidationError({"llego_hasta": "La zona de entrega es requerida."})
        if isinstance(llego_hasta_raw, (list, tuple)):
            attrs["llego_hasta"] = ", ".join(str(c).strip() for c in llego_hasta_raw if str(c).strip())
        else:
            attrs["llego_hasta"] = str(llego_hasta_raw).strip()

        cvu_val = (
            attrs.get("cvu")
            or self.initial_data.get("cvu")
            or self.initial_data.get("alias_bancario")
            or self.initial_data.get("alias")
        )
        if not cvu_val or not str(cvu_val).strip():
            raise serializers.ValidationError({"cvu": "El Alias o CVU/CBU bancario es requerido."})
        attrs["cvu"] = str(cvu_val).strip()

        return attrs