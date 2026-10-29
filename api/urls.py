from django.urls import (path, include)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (TokenRefreshView, TokenVerifyView)
from drf_spectacular.views import (SpectacularAPIView, SpectacularSwaggerView)
from .views import (
    ProductViewSet, 
    CategoryViewSet,
    CartViewSet,
    OrderViewSet,
    NotificacionViewSet,
    ModeracionProductoViewSet,
    MisComprasView,
    MisVentasView,
    ConfirmarEntregaView,
)
from core.views import (
    RegistroView, 
    LoginView, 
    UsuarioMeView, 
    SerVendedorView,
)

# Router para los endpoints basados en ViewSets (Tienda / Repilche)
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'productos', ProductViewSet, basename='producto')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'categorias', CategoryViewSet, basename='categoria')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'pedidos', OrderViewSet, basename='pedido')
router.register(r'notifications', NotificacionViewSet, basename='notification')
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')
router.register(
    r'moderation/products',
    ModeracionProductoViewSet,
    basename='moderation-product',
)
router.register(
    r'moderacion/productos',
    ModeracionProductoViewSet,
    basename='moderacion-producto',
)

urlpatterns = [
    # Autenticación y Cuentas (core)
    path("registro/", RegistroView.as_view(), name="registro"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("usuario/me/", UsuarioMeView.as_view(), name="usuario-me"),
    path("vendedor/", SerVendedorView.as_view(), name="ser-vendedor"),

    # Checkout seguro y Consultas C2C (Persona 3)
    path("pedidos/checkout/", OrderViewSet.as_view({"post": "create"}), name="pedido-checkout"),
    path("pedidos/crear/", OrderViewSet.as_view({"post": "create"}), name="pedido-crear"),
    path("mis-compras/", MisComprasView.as_view(), name="mis-compras"),
    path("mis-ventas/", MisVentasView.as_view(), name="mis-ventas"),
    path("ventas/<int:item_id>/confirmar-entrega/", ConfirmarEntregaView.as_view(), name="confirmar-entrega"),

    # Panel Administrativo y Métricas
    path("admin/dashboard/", ModeracionProductoViewSet.as_view({"get": "dashboard"}), name="admin-dashboard"),

    # Documentación OpenAPI / Swagger
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # Endpoints de la Tienda (Repilche)
    path("", include(router.urls)),
]