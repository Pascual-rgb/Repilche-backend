from rest_framework import serializers
from Repilche.models import Producto
from .categoria import CategorySerializer


class ProductSerializer(serializers.ModelSerializer):
    categoria_detail = CategorySerializer(source='categoria', read_only=True)
    
    name = serializers.CharField(source='nombre', read_only=True)
    description = serializers.CharField(source='descripcion', read_only=True)
    price = serializers.DecimalField(source='precio', max_digits=10, decimal_places=2, read_only=True)
    img = serializers.ImageField(source='imagen', read_only=True)

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
            "img",
            "estado",
            "justificacion",
            "creado_el",
        ]
        read_only_fields = ["id", "vendedor", "creado_el"]

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.is_authenticated or not user.is_vendedor:
            raise serializers.ValidationError("Debe ser un usuario vendedor registrado para publicar prendas.")
        return attrs

    def create(self, validated_data):
        validated_data['vendedor'] = self.context['request'].user
        return super().create(validated_data)