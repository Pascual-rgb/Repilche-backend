from rest_framework import serializers
from Repilche.models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    descripcion = serializers.CharField(source="mensaje", read_only=True)
    created_at = serializers.DateTimeField(source="creado_el", read_only=True)

    class Meta:
        model = Notificacion
        fields = [
            "id",
            "usuario",
            "tipo",
            "titulo",
            "mensaje",
            "descripcion",
            "leida",
            "creado_el",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "usuario",
            "tipo",
            "titulo",
            "mensaje",
            "descripcion",
            "creado_el",
            "created_at",
        ]
