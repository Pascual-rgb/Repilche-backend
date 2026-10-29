from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from Repilche.models import Producto
from Repilche.notificaciones import notificar
from api.serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    Endpoint completo para productos.
    - Lectura pública para cualquier usuario (ReadOnly para listar).
    - Creación/Modificación restringida a usuarios con is_vendedor=True.
    - Moderación de prendas restringida a administradores (is_staff=True).
    """
    queryset = Producto.objects.filter(
        estado=Producto.Estado.DISPONIBLE,
        stock__gt=0,
        estado_moderacion=Producto.EstadoModeracion.APROBADO,
    ).select_related('vendedor', 'categoria').order_by('-creado_el')
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'descripcion', 'vendedor__first_name']

    def get_permissions(self):
        if self.action in ['pendientes', 'aprobar', 'rechazar']:
            return [permissions.IsAdminUser()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        if self.action in ['pendientes', 'aprobar', 'rechazar']:
            return Producto.objects.all().select_related('vendedor', 'categoria')

        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get('categoria')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)

        mis_productos = self.request.query_params.get('mis_productos')
        if mis_productos and self.request.user.is_authenticated:
            queryset = Producto.objects.filter(vendedor=self.request.user).order_by('-creado_el')

        return queryset

    def perform_create(self, serializer):
        producto = serializer.save()
        notificar(
            usuario=producto.vendedor,
            titulo="Prenda en revisión",
            mensaje=f'Estamos evaluando tu publicación "{producto.nombre}". Te notificaremos cuando sea moderada.',
            tipo="MODERACION",
        )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser], url_path='pendientes')
    def pendientes(self, request):
        """Lista todas las prendas pendientes de moderación para administradores."""
        queryset = Producto.objects.filter(
            estado_moderacion=Producto.EstadoModeracion.PENDIENTE
        ).select_related('vendedor', 'categoria').order_by('creado_el')

        data = []
        for p in queryset:
            item = self.get_serializer(p).data
            # Asegurar que vendedor sea string legible para la interfaz
            vendedor_nombre = ""
            if p.vendedor:
                vendedor_nombre = (
                    p.vendedor.get_full_name().strip()
                    or p.vendedor.username
                    or p.vendedor.email
                )
            item['vendedor'] = vendedor_nombre or str(p.vendedor_id or "")
            data.append(item)

        return Response(data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser], url_path='aprobar')
    @transaction.atomic
    def aprobar(self, request, pk=None):
        """Aprueba una prenda pendiente y notifica al vendedor."""
        producto = self.get_object()
        if producto.estado_moderacion != Producto.EstadoModeracion.PENDIENTE:
            return Response(
                {"error": "Solo se pueden aprobar prendas pendientes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        producto.estado_moderacion = Producto.EstadoModeracion.APROBADO
        producto.moderado_el = timezone.now()
        producto.motivo_rechazo = ""
        producto.save(update_fields=["estado_moderacion", "moderado_el", "motivo_rechazo"])

        notificar(
            usuario=producto.vendedor,
            titulo="¡Tu prenda fue aprobada!",
            mensaje=f'Tu publicación "{producto.nombre}" ya está visible y disponible para la compra en Repilche.',
            tipo="MODERACION",
        )
        return Response(self.get_serializer(producto).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser], url_path='rechazar')
    @transaction.atomic
    def rechazar(self, request, pk=None):
        """Rechaza una prenda con motivo justificado y notifica al vendedor."""
        motivo = request.data.get("motivo", "")
        if not isinstance(motivo, str) or not motivo.strip():
            return Response(
                {"motivo": ["Este campo es obligatorio."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        producto = self.get_object()
        producto.estado_moderacion = Producto.EstadoModeracion.RECHAZADO
        producto.motivo_rechazo = motivo.strip()
        producto.moderado_el = timezone.now()
        producto.save(update_fields=["estado_moderacion", "motivo_rechazo", "moderado_el"])

        notificar(
            usuario=producto.vendedor,
            titulo="Tu prenda no fue aprobada",
            mensaje=f'Tu publicación "{producto.nombre}" fue rechazada. Motivo: {producto.motivo_rechazo}',
            tipo="MODERACION",
        )
        return Response(self.get_serializer(producto).data)