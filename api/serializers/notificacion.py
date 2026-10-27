from rest_framework import serializers
from Repilche.models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
<<<<<<< HEAD
        fields = ["id", "usuario", "tipo", "titulo", "mensaje", "leida", "creado_el"]
        read_only_fields = ["id", "usuario", "tipo", "titulo", "mensaje", "creado_el"]
=======
        fields = ["id", "tipo", "titulo", "mensaje", "leida", "creado_el"]
        read_only_fields = ["id", "tipo", "titulo", "mensaje", "creado_el"]
>>>>>>> 31e1b1cdfd6ff718db8e2774b695f6b86e83e0e3
