from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import PerfilVendedor
from core.serializers import PerfilVendedorSerializer


class SerVendedorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        data = {
            "localidad": request.data.get("locality") or request.data.get("localidad"),
            "llego_hasta": request.data.get("llegoHasta") or request.data.get("llego_hasta"),
            "cvu": request.data.get("cvu"),
            "descripcion": request.data.get("description") or request.data.get("descripcion", ""),
        }

        perfil, created = PerfilVendedor.objects.get_or_create(usuario=user, defaults=data)
        if not created:
            for key, value in data.items():
                if value is not None:
                    setattr(perfil, key, value)
            perfil.save()

        if not user.is_vendedor:
            user.is_vendedor = True
            user.save(update_fields=["is_vendedor"])

        serializer = PerfilVendedorSerializer(perfil)
        return Response(
            {
                "mensaje": "¡Felicitaciones! Ahora sos vendedor en Repilche.",
                "perfil_vendedor": serializer.data,
                "is_vendedor": True,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )