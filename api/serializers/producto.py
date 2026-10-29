from rest_framework import serializers
from Repilche.models import Producto
from .categoria import CategorySerializer


class ProductSerializer(serializers.ModelSerializer):
    categoria_detail = CategorySerializer(source='categoria', read_only=True)
    
    name = serializers.CharField(source='nombre', read_only=True)
    description = serializers.CharField(source='descripcion', read_only=True)
    price = serializers.DecimalField(source='precio', max_digits=10, decimal_places=2, read_only=True)
    # Salida para el frontend (lectura)
    imagen_url = serializers.CharField(source='imagen', read_only=True)
    img = serializers.CharField(source='imagen', read_only=True)

    # Campos de moderación y compatibilidad
    justificacion = serializers.CharField(source='motivo_rechazo', read_only=True)
    justificacion_rechazo = serializers.CharField(source='motivo_rechazo', read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id",
            "vendedor",
            "categoria",
            "categoria_detail",
            "nombre",
            "name",
            "descripcion",
            "description",
            "precio",
            "price",
            "stock",
            "imagen",
            "imagen_url",
            "img",
            "estado",
            "estado_moderacion",
            "motivo_rechazo",
            "justificacion",
            "justificacion_rechazo",
            "moderado_el",
            "creado_el",
        ]
        read_only_fields = [
            "id",
            "vendedor",
            "creado_el",
            "motivo_rechazo",
            "justificacion",
            "justificacion_rechazo",
            "moderado_el",
        ]

    def to_internal_value(self, data):
        # Si el frontend envía 'imagen_url' o 'img', lo normalizamos a 'imagen' antes de validar
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'imagen_url' in data and not data.get('imagen'):
            data['imagen'] = data['imagen_url']
        elif 'img' in data and not data.get('imagen'):
            data['imagen'] = data['img']
        return super().to_internal_value(data)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.is_authenticated or not user.is_vendedor:
            raise serializers.ValidationError("Debe ser un usuario vendedor registrado para publicar prendas.")
        return attrs

    def create(self, validated_data):
        validated_data['vendedor'] = self.context['request'].user
        return super().create(validated_data)