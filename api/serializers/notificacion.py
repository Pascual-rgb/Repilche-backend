from rest_framework import serializers
from Repilche.models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ["id", "tipo", "titulo", "mensaje", "leida", "creado_el"]
        read_only_fields = ["id", "tipo", "titulo", "mensaje", "creado_el"]
