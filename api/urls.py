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
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'notifications', NotificacionViewSet, basename='notification')

urlpatterns = [
    # Autenticación y Cuentas (core)
    path("registro/", RegistroView.as_view(), name="registro"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("usuario/me/", UsuarioMeView.as_view(), name="usuario-me"),
    path("vendedor/", SerVendedorView.as_view(), name="ser-vendedor"),

    # Documentación OpenAPI / Swagger
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # Endpoints de la Tienda (Repilche)
    path("", include(router.urls)),
]