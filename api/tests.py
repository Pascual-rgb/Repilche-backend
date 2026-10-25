from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from Repilche.models import Categoria, Notificacion, Producto

User = get_user_model()


class AuthAndUserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("registro")
        self.login_url = reverse("login")
        self.token_verify_url = reverse("token-verify")
        self.me_url = reverse("usuario-me")
        self.vendedor_url = reverse("ser-vendedor")

    def test_token_verify_acepta_access_valido_y_rechaza_invalido(self):
        user = User.objects.create_user(
            email="verify@repilche.com",
            password="TestPassword123!",
        )
        access_token = str(RefreshToken.for_user(user).access_token)

        valid_response = self.client.post(
            self.token_verify_url,
            {"token": access_token},
            format="json",
        )
        invalid_response = self.client.post(
            self.token_verify_url,
            {"token": "token-invalido"},
            format="json",
        )

        self.assertEqual(valid_response.status_code, status.HTTP_200_OK)
        self.assertEqual(invalid_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_registro_usuario_con_form_frontend(self):
        """Prueba registro usando las claves de RegistroForm.tsx (name, lastName, numberPhone)."""
        payload = {
            "name": "Valentino",
            "lastName": "Rossi",
            "numberPhone": "2804123456",
            "email": "valentino@repilche.com",
            "password": "PasswordSegura123!",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertEqual(response.data["user"]["email"], "valentino@repilche.com")
        self.assertEqual(response.data["user"]["first_name"], "Valentino")
        self.assertEqual(response.data["user"]["phone"], "2804123456")
        self.assertEqual(response.data["user"]["celphone"], "2804123456")
        self.assertFalse(response.data["user"]["is_vendedor"])

    def test_registro_devuelve_tokens_en_raiz_y_access_autentica_perfil(self):
        payload = {
            "name": "Valentino",
            "lastName": "Rossi",
            "numberPhone": "2804123456",
            "email": "registro-token@repilche.com",
            "password": "PasswordSegura123!",
        }

        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["access"], response.data["tokens"]["access"])
        self.assertEqual(response.data["refresh"], response.data["tokens"]["refresh"])

        profile_response = self.client.get(
            self.me_url,
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
        )

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["email"], payload["email"])

    def test_registro_usuario_con_celphone(self):
        """Prueba registro usando celphone como clave de celular."""
        payload = {
            "name": "Martin",
            "lastName": "Gomez",
            "celphone": "2804987654",
            "email": "martin@repilche.com",
            "password": "PasswordSegura123!",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["phone"], "2804987654")

    def test_registro_con_email_existente_devuelve_error_en_email(self):
        User.objects.create_user(
            email="existente@repilche.com",
            password="PasswordSegura123!",
        )
        payload = {
            "name": "Otra",
            "lastName": "Persona",
            "numberPhone": "2804123456",
            "email": "existente@repilche.com",
            "password": "PasswordSegura123!",
        }

        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registro_con_contrasena_debil_devuelve_error_en_password(self):
        payload = {
            "name": "Otra",
            "lastName": "Persona",
            "numberPhone": "2804123456",
            "email": "debil@repilche.com",
            "password": "123",
        }

        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registro_falla_sin_telefono_o_celular(self):
        """El registro DEBE fallar si no se envía teléfono o celular."""
        payload = {
            "name": "Martin",
            "lastName": "Gomez",
            "email": "sin_tel@repilche.com",
            "password": "PasswordSegura123!",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("numberPhone", response.data)

    def test_login_con_email_devuelve_jwt_y_usuario(self):
        """Prueba autenticación con email y contraseña devolviendo JWT y perfil."""
        user = User.objects.create_user(
            email="ivan@repilche.com",
            password="MiPassword123!",
            first_name="Ivan",
            last_name="Pascualich",
        )
        payload = {
            "email": "ivan@repilche.com",
            "password": "MiPassword123!",
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "ivan@repilche.com")
        self.assertEqual(response.data["user"]["first_name"], "Ivan")

    def test_login_con_contrasena_incorrecta_devuelve_401(self):
        User.objects.create_user(
            email="login-incorrecto@repilche.com",
            password="PasswordSegura123!",
        )

        response = self.client.post(
            self.login_url,
            {
                "email": "login-incorrecto@repilche.com",
                "password": "ContrasenaIncorrecta123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_contrasena_se_guarda_hasheada_y_puede_verificarse(self):
        payload = {
            "name": "Usuario",
            "lastName": "Prueba",
            "numberPhone": "2804123456",
            "email": "hash@repilche.com",
            "password": "PasswordSegura123!",
        }

        response = self.client.post(self.register_url, payload, format="json")
        user = User.objects.get(email=payload["email"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(user.password.startswith("pbkdf2_"))
        self.assertTrue(user.check_password(payload["password"]))

    def test_perfil_usuario_me_y_editar_perfil(self):
        """Prueba consultar y editar perfil con token JWT."""
        user = User.objects.create_user(
            email="ezequiel@repilche.com",
            password="Password123!",
            first_name="Ezequiel",
            last_name="Martinez",
        )
        self.client.force_authenticate(user=user)

        # GET /api/usuario/me/
        get_res = self.client.get(self.me_url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data["email"], "ezequiel@repilche.com")

        # PATCH /api/usuario/me/ (editar username y teléfono)
        patch_res = self.client.patch(
            self.me_url,
            {"usuario": "ezequiel_mn", "numberPhone": "2804998877"},
            format="json",
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.username, "ezequiel_mn")
        self.assertEqual(user.phone, "2804998877")

    def test_ser_vendedor_activa_rol_y_crea_perfil(self):
        """Prueba envío del formulario /ser-vendedor."""
        user = User.objects.create_user(
            email="vendedor@repilche.com",
            password="Password123!",
            first_name="Comprador",
            last_name="Nuevo",
        )
        self.client.force_authenticate(user=user)
        self.assertFalse(user.is_vendedor)

        payload = {
            "locality": "Trelew",
            "llegoHasta": "Plaza Centenario y Rawson",
            "cvu": "0000003100012345678901",
            "description": "Ropa vintage y retro en excelente estado.",
        }
        response = self.client.post(self.vendedor_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_vendedor"])

        user.refresh_from_db()
        self.assertTrue(user.is_vendedor)
        self.assertEqual(user.perfil_vendedor.localidad, "Trelew")
        self.assertEqual(user.perfil_vendedor.cvu, "0000003100012345678901")


class TiendaTests(TestCase):
    """Pruebas de consulta de productos y categorías."""

    def setUp(self):
        self.client = APIClient()
        # Limpiamos para asegurar el entorno aislado de la prueba
        Producto.objects.all().delete()
        Categoria.objects.all().delete()
        
        self.categoria = Categoria.objects.create(nombre="Remeras", slug="remeras")
        self.vendedor = User.objects.create_user(
            email="vendedor_tienda@repilche.com",
            password="Password123!",
            first_name="Carlos",
            last_name="Perez",
            is_vendedor=True,
        )
        self.producto = Producto.objects.create(
            vendedor=self.vendedor,
            categoria=self.categoria,
            nombre="Remera Oversize Vintage",
            descripcion="100% algodón",
            precio=15000.00,
            stock=5,
            estado_moderacion="APROBADO",
        )

    def test_listar_categorias(self):
        response = self.client.get(reverse("category-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Extraer resultados si está paginado, o usar la data directa si es lista
        data = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["nombre"], "Remeras")

    def test_listar_productos(self):
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["nombre"], self.producto.nombre)

    def test_listar_productos_no_incluye_productos_pendientes(self):
        Producto.objects.create(
            vendedor=self.vendedor,
            categoria=self.categoria,
            nombre="Producto pendiente",
            descripcion="A la espera de moderación",
            precio=12000.00,
            stock=1,
        )

        response = self.client.get(reverse("product-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["results"] if isinstance(response.data, dict) else response.data
        nombres = [producto["nombre"] for producto in data]
        self.assertNotIn("Producto pendiente", nombres)
        self.assertIn(self.producto.nombre, nombres)

class CarritoYCheckoutTests(TestCase):
    """Pruebas para la gestión del carrito de compras y el proceso de checkout/órdenes."""

    def setUp(self):
        self.client = APIClient()
        self.categoria = Categoria.objects.create(nombre="Pantalones", slug="pantalones")
        self.vendedor = User.objects.create_user(
            email="vendedor_checkout@repilche.com",
            password="Password123!",
            first_name="Lucía",
            last_name="Giménez",
            is_vendedor=True,
        )
        self.comprador = User.objects.create_user(
            email="comprador@repilche.com",
            password="Password123!",
            first_name="Marcos",
            last_name="Sosa",
        )
        self.producto = Producto.objects.create(
            vendedor=self.vendedor,
            categoria=self.categoria,
            nombre="Jeans Vintage 90s",
            descripcion="Talle 40, tiro alto",
            precio=25000.00,
            stock=2,
            estado_moderacion="APROBADO",
        )
        self.cart_add_url = reverse("cart-add-item")
        self.cart_list_url = reverse("cart-list")
        self.order_list_url = reverse("order-list")

    def test_agregar_producto_al_carrito_y_verificar_totales(self):
        self.client.force_authenticate(user=self.comprador)
        
        # Agregar producto al carrito
        payload = {"producto_id": self.producto.id, "cantidad": 2}
        response = self.client.post(self.cart_add_url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_items"], 2)
        self.assertEqual(float(response.data["total"]), 50000.00)

    def test_checkout_exitoso_genera_orden_descuenta_stock_y_vacía_carrito(self):
        self.client.force_authenticate(user=self.comprador)
        
        # 1. Agregar al carrito
        self.client.post(self.cart_add_url, {"producto_id": self.producto.id, "cantidad": 1}, format="json")
        
        # 2. Realizar orden (Checkout)
        order_response = self.client.post(self.order_list_url, {"alias_pago": "marcos.mp"}, format="json")
        
        self.assertEqual(order_response.status_code, status.HTTP_201_CREATED)
        self.assertIn("codigo_secreto", order_response.data)
        # Validar que el código secreto generado tenga exactamente 6 caracteres/dígitos
        self.assertEqual(len(order_response.data["codigo_secreto"]), 6)
        self.assertEqual(float(order_response.data["total"]), 25000.00)

        # 3. Verificar que el stock del producto disminuyó (de 2 a 1)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 1)

        # 4. Verificar que el carrito quedó vacío
        cart_response = self.client.get(self.cart_list_url)
        self.assertEqual(cart_response.data["total_items"], 0)

    def test_checkout_falla_si_no_hay_stock_suficiente(self):
        self.client.force_authenticate(user=self.comprador)
        
        # Intentar comprar más de lo que hay en stock (stock inicial es 2, pedimos 5)
        self.client.post(self.cart_add_url, {"producto_id": self.producto.id, "cantidad": 5}, format="json")
        
        # Intentar hacer checkout
        order_response = self.client.post(self.order_list_url, {"alias_pago": "marcos.mp"}, format="json")
        
        self.assertEqual(order_response.status_code, status.HTTP_400_BAD_REQUEST)


class NotificacionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            email="notificaciones@repilche.com",
            password="PasswordSegura123!",
            first_name="Usuario",
            last_name="Notificaciones",
        )
        self.otro_usuario = User.objects.create_user(
            email="otro-notificaciones@repilche.com",
            password="PasswordSegura123!",
            first_name="Otro",
            last_name="Usuario",
        )
        self.list_url = reverse("notification-list")
        self.primera = Notificacion.objects.create(
            usuario=self.usuario,
            titulo="Primera",
            mensaje="Notificación más vieja.",
        )
        self.segunda = Notificacion.objects.create(
            usuario=self.usuario,
            titulo="Segunda",
            mensaje="Notificación más nueva.",
        )
        Notificacion.objects.create(
            usuario=self.otro_usuario,
            titulo="Ajena",
            mensaje="Notificación de otra cuenta.",
        )
        self.primera.creado_el = self.primera.creado_el.replace(year=2020)
        self.segunda.creado_el = self.segunda.creado_el.replace(year=2021)
        Notificacion.objects.filter(pk=self.primera.pk).update(creado_el=self.primera.creado_el)
        Notificacion.objects.filter(pk=self.segunda.pk).update(creado_el=self.segunda.creado_el)

    def test_listado_solo_devuelve_notificaciones_propias_ordenadas_por_fecha(self):
        self.client.force_authenticate(user=self.usuario)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertEqual(
            [notificacion["id"] for notificacion in data],
            [self.segunda.id, self.primera.id],
        )
        self.assertEqual(
            [notificacion["titulo"] for notificacion in data],
            ["Segunda", "Primera"],
        )

    def test_patch_marca_notificacion_como_leida(self):
        self.client.force_authenticate(user=self.usuario)

        response = self.client.patch(
            reverse("notification-detail", args=[self.primera.id]),
            {"leida": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["leida"])
        self.primera.refresh_from_db()
        self.assertTrue(self.primera.leida)

    def test_patch_notificacion_ajena_devuelve_404(self):
        notificacion_ajena = Notificacion.objects.get(usuario=self.otro_usuario)
        self.client.force_authenticate(user=self.usuario)

        response = self.client.patch(
            reverse("notification-detail", args=[notificacion_ajena.id]),
            {"leida": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_listado_sin_token_devuelve_401(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_y_delete_no_estan_permitidos(self):
        self.client.force_authenticate(user=self.usuario)
        detail_url = reverse("notification-detail", args=[self.primera.id])

        put_response = self.client.put(
            detail_url,
            {"leida": True},
            format="json",
        )
        delete_response = self.client.delete(detail_url)

        self.assertEqual(put_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(delete_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)