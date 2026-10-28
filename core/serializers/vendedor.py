from rest_framework import serializers
from core.models import PerfilVendedor


class PerfilVendedorSerializer(serializers.ModelSerializer):
    locality = serializers.CharField(source="localidad", required=False, allow_blank=True)
    llegoHasta = serializers.CharField(source="llego_hasta", required=False, allow_blank=True)
    description = serializers.CharField(source="descripcion", required=False, allow_blank=True)
    alias_bancario = serializers.CharField(source="cvu", required=False, allow_blank=True)
    alias = serializers.CharField(source="cvu", required=False, allow_blank=True)

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
            "localidad": {"required": False, "allow_blank": True},
            "llego_hasta": {"required": False, "allow_blank": True},
            "cvu": {"required": False, "allow_blank": True},
            "descripcion": {"required": False, "allow_blank": True},
        }

    def to_internal_value(self, data):
        if hasattr(data, "dict"):
            data = data.dict()
        elif isinstance(data, dict):
            data = data.copy()
        else:
            try:
                data = dict(data)
            except Exception:
                data = {}

        # Mapeo de campos camelCase / alias frontend -> campos del modelo
        if "locality" in data and "localidad" not in data:
            data["localidad"] = data["locality"]

        llego = data.get("llegoHasta") if "llegoHasta" in data else data.get("llego_hasta")
        if isinstance(llego, (list, tuple)):
            data["llego_hasta"] = ", ".join(str(c).strip() for c in llego if str(c).strip())
            data["llegoHasta"] = data["llego_hasta"]
        elif "llegoHasta" in data and "llego_hasta" not in data:
            data["llego_hasta"] = data["llegoHasta"]

        alias_val = (
            data.get("alias")
            if "alias" in data
            else (data.get("alias_bancario") if "alias_bancario" in data else data.get("cvu"))
        )
        if alias_val is not None:
            data["cvu"] = alias_val
            data["alias"] = alias_val
            data["alias_bancario"] = alias_val

        if "description" in data and "descripcion" not in data:
            data["descripcion"] = data["description"]
        if "descripcion" in data and "description" not in data:
            data["description"] = data["descripcion"]

        return super().to_internal_value(data)

    def validate(self, attrs):
        localidad = attrs.get("localidad") or self.initial_data.get("locality") or self.initial_data.get("localidad")
        if not localidad or not str(localidad).strip():
            raise serializers.ValidationError({"localidad": "La localidad es requerida."})
        attrs["localidad"] = str(localidad).strip()

        llego_hasta_raw = attrs.get("llego_hasta") or self.initial_data.get("llegoHasta") or self.initial_data.get("llego_hasta")
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

        desc_val = (
            attrs.get("descripcion")
            if attrs.get("descripcion") is not None
            else (self.initial_data.get("description") or self.initial_data.get("descripcion") or "")
        )
        attrs["descripcion"] = str(desc_val).strip()

        return attrs

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["locality"] = instance.localidad
        ret["llegoHasta"] = instance.llego_hasta
        ret["alias"] = instance.cvu
        ret["alias_bancario"] = instance.cvu
        ret["description"] = instance.descripcion
        return ret