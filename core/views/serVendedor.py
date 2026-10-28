from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import PerfilVendedor
from core.serializers import PerfilVendedorSerializer


class SerVendedorView(APIView):
    """
    POST /api/vendedor/ -> Registra o actualiza el perfil de vendedor del usuario autenticado.
    GET /api/vendedor/  -> Devuelve el perfil y estado de vendedor del usuario.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        perfil = getattr(user, "perfil_vendedor", None)
        if not perfil:
            return Response(
                {"is_vendedor": bool(user.is_vendedor), "perfil_vendedor": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "is_vendedor": bool(user.is_vendedor),
                "perfil_vendedor": PerfilVendedorSerializer(perfil).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        try:
            user = request.user
            data = request.data if isinstance(request.data, dict) else {}

            serializer = PerfilVendedorSerializer(data=data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data

            # Extracción robusta de campos para garantizar que NINGUNO sea NULL en PostgreSQL
            localidad = (
                validated_data.get("localidad")
                or data.get("locality")
                or data.get("localidad")
                or ""
            )
            llego_hasta = (
                validated_data.get("llego_hasta")
                or data.get("llegoHasta")
                or data.get("llego_hasta")
                or ""
            )
            if isinstance(llego_hasta, (list, tuple)):
                llego_hasta = ", ".join(str(c).strip() for c in llego_hasta if str(c).strip())

            alias = data.get("alias") or data.get("alias_bancario") or ""
            cvu = validated_data.get("cvu") or data.get("cvu") or alias or ""

            descripcion = (
                validated_data.get("descripcion")
                or data.get("description")
                or data.get("descripcion")
                or ""
            )

            defaults = {
                "localidad": str(localidad).strip(),
                "llego_hasta": str(llego_hasta).strip(),
                "cvu": str(cvu).strip(),
                "descripcion": str(descripcion).strip(),
            }

            # update_or_create previene colisiones de integridad OneToOne si el usuario ya tiene perfil previo
            perfil, created = PerfilVendedor.objects.update_or_create(
                usuario=user,
                defaults=defaults,
            )

            # Activar el estado de vendedor en el usuario y persistir
            user.is_vendedor = True
            user.save(update_fields=["is_vendedor"])

            return Response(
                {
                    "mensaje": "Vendedor registrado exitosamente.",
                    "perfil_vendedor": PerfilVendedorSerializer(perfil).data,
                    "is_vendedor": True,
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        except ValidationError as exc:
            return Response(
                exc.detail if hasattr(exc, "detail") else {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError as exc:
            return Response(
                {
                    "error": "Error de integridad de datos al guardar el perfil de vendedor.",
                    "detalle": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response(
                {
                    "error": "Ocurrió un error al procesar la solicitud de vendedor.",
                    "detalle": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )