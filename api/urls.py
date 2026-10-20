from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import (
    RegistroView,
    LoginView,
    UsuarioMeView,
    SerVendedorView,
)

urlpatterns = [
    # Autenticación y Cuentas
    path("registro/", RegistroView.as_view(), name="registro"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("usuario/me/", UsuarioMeView.as_view(), name="usuario-me"),
    path("vendedor/", SerVendedorView.as_view(), name="ser-vendedor"),

    # Documentación OpenAPI / Swagger
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
