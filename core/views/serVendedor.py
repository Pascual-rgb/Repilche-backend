from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import PerfilVendedor
from core.serializers import PerfilVendedorSerializer


class SerVendedorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = PerfilVendedorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        perfil, created = PerfilVendedor.objects.get_or_create(usuario=user, defaults=validated_data)
        if not created:
            for key, value in validated_data.items():
                setattr(perfil, key, value)
            perfil.save()

        if not user.is_vendedor:
            user.is_vendedor = True
            user.save(update_fields=["is_vendedor"])

        return Response(
            {
                "mensaje": "¡Felicitaciones! Ahora sos vendedor en Repilche.",
                "perfil_vendedor": PerfilVendedorSerializer(perfil).data,
                "is_vendedor": True,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )