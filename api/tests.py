from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from Repilche.models import Categoria, Notificacion, Producto, Pedido, ItemPedido

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
        # El código secreto ahora es por ítem: 6 dígitos numéricos
        codigo = order_response.data["items"][0]["codigo_secreto"]
        self.assertEqual(len(codigo), 6)
        self.assertTrue(codigo.isdigit())
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


class CheckoutSeguroTests(TestCase):
    """Tarea 1 (Persona 3): POST /api/pedidos/checkout/."""

    def setUp(self):
        from Repilche.models import Carrito, ItemCarrito
        self.client = APIClient()
        self.url = reverse("pedido-checkout")
        categoria = Categoria.objects.create(nombre="Abrigos", slug="abrigos")
        self.vendedor = User.objects.create_user(
            email="vend_checkout@repilche.com", password="Password123!", is_vendedor=True
        )
        self.comprador = User.objects.create_user(
            email="comp_checkout@repilche.com", password="Password123!"
        )
        self.producto = Producto.objects.create(
            vendedor=self.vendedor, categoria=categoria, nombre="Campera de cuero",
            descripcion="Vintage", precio=80000, stock=1, estado_moderacion="APROBADO",
        )
        self.carrito = Carrito.objects.create(usuario=self.comprador)
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto, cantidad=1)
        self.client.force_authenticate(user=self.comprador)

    def test_checkout_crea_pedido_items_y_marca_vendido(self):
        from Repilche.models import ItemPedido, Pedido
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pedido = Pedido.objects.get(id=response.data["id"])
        self.assertEqual(pedido.estado_pago, Pedido.EstadoPago.PENDIENTE)
        self.assertEqual(float(pedido.total), 80000.00)

        item = ItemPedido.objects.get(pedido=pedido)
        self.assertEqual(item.vendedor, self.vendedor)
        self.assertEqual(item.estado_entrega, ItemPedido.EstadoEntrega.EN_CUSTODIA)
        self.assertRegex(item.codigo_secreto, r"^\d{6}$")

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 0)
        self.assertEqual(self.producto.estado, Producto.Estado.VENDIDO)
        self.assertFalse(self.carrito.items.exists())

        # Notifica a comprador (con su código) y a vendedor
        notif_comprador = Notificacion.objects.get(usuario=self.comprador)
        self.assertIn(item.codigo_secreto, notif_comprador.mensaje)
        self.assertEqual(notif_comprador.tipo, "PEDIDO")
        self.assertTrue(Notificacion.objects.filter(usuario=self.vendedor, tipo="PEDIDO").exists())

    def test_checkout_con_carrito_vacio_devuelve_400(self):
        self.carrito.items.all().delete()
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_rechaza_prenda_no_disponible_y_no_crea_nada(self):
        from Repilche.models import Pedido
        Producto.objects.filter(pk=self.producto.pk).update(estado="VENDIDO")

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Pedido.objects.exists())
        self.assertTrue(self.carrito.items.exists())

    def test_vendedor_no_puede_comprar_su_propia_prenda(self):
        from Repilche.models import Carrito, ItemCarrito
        carrito_vendedor = Carrito.objects.create(usuario=self.vendedor)
        ItemCarrito.objects.create(carrito=carrito_vendedor, producto=self.producto, cantidad=1)
        self.client.force_authenticate(user=self.vendedor)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ConsultasC2CTests(TestCase):
    """Tarea 3 (Persona 3): Endpoints de Consulta C2C: /api/mis-compras/ y /api/mis-ventas/."""

    def setUp(self):
        from Repilche.models import ItemPedido, Pedido
        self.client = APIClient()
        self.compras_url = reverse("mis-compras")
        self.ventas_url = reverse("mis-ventas")

        self.categoria = Categoria.objects.create(nombre="Calzado", slug="calzado")
        self.vendedor = User.objects.create_user(
            email="vendedor_c2c@repilche.com",
            password="Password123!",
            first_name="Carlos",
            last_name="Vendedor",
            is_vendedor=True,
        )
        self.comprador = User.objects.create_user(
            email="comprador_c2c@repilche.com",
            password="Password123!",
            first_name="Ana",
            last_name="Compradora",
        )
        self.otro_usuario = User.objects.create_user(
            email="otro_c2c@repilche.com",
            password="Password123!",
        )

        self.producto = Producto.objects.create(
            vendedor=self.vendedor,
            categoria=self.categoria,
            nombre="Zapatillas Urbanas",
            descripcion="Talle 41",
            precio=45000,
            stock=1,
            estado=Producto.Estado.VENDIDO,
            estado_moderacion="APROBADO",
        )

        self.pedido = Pedido.objects.create(
            comprador=self.comprador,
            total=45000,
            estado_pago=Pedido.EstadoPago.PENDIENTE,
        )

        self.item = ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            vendedor=self.vendedor,
            nombre_producto=self.producto.nombre,
            precio_unitario=self.producto.precio,
            cantidad=1,
            codigo_secreto="654321",
            estado_entrega=ItemPedido.EstadoEntrega.EN_CUSTODIA,
        )

    def test_endpoints_c2c_requieren_autenticacion(self):
        resp_compras = self.client.get(self.compras_url)
        resp_ventas = self.client.get(self.ventas_url)

        self.assertEqual(resp_compras.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp_ventas.status_code, status.HTTP_401_UNAUTHORIZED)

    def _results(self, response):
        return response.data["results"] if isinstance(response.data, dict) and "results" in response.data else response.data

    def test_mis_compras_muestra_codigo_secreto_y_datos_del_vendedor(self):
        self.client.force_authenticate(user=self.comprador)
        response = self.client.get(self.compras_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._results(response)
        self.assertEqual(len(results), 1)

        item_data = results[0]
        self.assertEqual(item_data["id"], self.item.id)
        self.assertEqual(item_data["nombre_producto"], "Zapatillas Urbanas")
        self.assertEqual(float(item_data["precio_unitario"]), 45000.00)
        self.assertEqual(item_data["estado_entrega"], "en_custodia")

        # El comprador DEBE ver el código numérico de 6 dígitos
        self.assertEqual(item_data["codigo_secreto"], "654321")
        self.assertEqual(len(item_data["codigo_secreto"]), 6)
        self.assertTrue(item_data["codigo_secreto"].isdigit())

        # Datos del vendedor visibles para coordinar entrega
        self.assertEqual(item_data["vendedor"]["email"], self.vendedor.email)
        self.assertEqual(item_data["vendedor"]["first_name"], "Carlos")

    def test_mis_ventas_oculta_codigo_secreto_y_muestra_comprador(self):
        self.client.force_authenticate(user=self.vendedor)
        response = self.client.get(self.ventas_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._results(response)
        self.assertEqual(len(results), 1)

        venta_data = results[0]
        self.assertEqual(venta_data["id"], self.item.id)
        self.assertEqual(venta_data["nombre_producto"], "Zapatillas Urbanas")
        self.assertEqual(venta_data["estado_entrega"], "en_custodia")

        # El vendedor NUNCA debe ver el código secreto en su listado
        self.assertNotIn("codigo_secreto", venta_data)

        # Datos del comprador visibles para coordinar entrega
        self.assertEqual(venta_data["comprador"]["email"], self.comprador.email)
        self.assertEqual(venta_data["comprador"]["first_name"], "Ana")

    def test_aislamiento_de_usuarios_no_muestra_datos_ajenos(self):
        self.client.force_authenticate(user=self.otro_usuario)

        resp_compras = self.client.get(self.compras_url)
        resp_ventas = self.client.get(self.ventas_url)

        self.assertEqual(resp_compras.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self._results(resp_compras)), 0)
        self.assertEqual(resp_ventas.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self._results(resp_ventas)), 0)


class ConfirmarEntregaTests(TestCase):
    """Tarea 2 (Persona 3): Confirmación de Entrega POST /api/ventas/<item_id>/confirmar-entrega/."""

    def setUp(self):
        from Repilche.models import ItemPedido, Pedido
        self.client = APIClient()

        self.categoria = Categoria.objects.create(nombre="Ropa de Abrigo", slug="abrigo-c2c")
        self.vendedor = User.objects.create_user(
            email="vendedor_entrega@repilche.com",
            password="Password123!",
            first_name="Marcos",
            is_vendedor=True,
        )
        self.comprador = User.objects.create_user(
            email="comprador_entrega@repilche.com",
            password="Password123!",
            first_name="Lucia",
        )
        self.ajeno = User.objects.create_user(
            email="ajeno_entrega@repilche.com",
            password="Password123!",
        )

        self.producto = Producto.objects.create(
            vendedor=self.vendedor,
            categoria=self.categoria,
            nombre="Buzo Oversize",
            descripcion="Negro talle L",
            precio=35000,
            stock=0,
            estado=Producto.Estado.VENDIDO,
            estado_moderacion="APROBADO",
        )

        self.pedido = Pedido.objects.create(
            comprador=self.comprador,
            total=35000,
            estado_pago=Pedido.EstadoPago.PENDIENTE,
        )

        self.item = ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            vendedor=self.vendedor,
            nombre_producto=self.producto.nombre,
            precio_unitario=self.producto.precio,
            cantidad=1,
            codigo_secreto="987654",
            estado_entrega=ItemPedido.EstadoEntrega.EN_CUSTODIA,
        )

        self.url = reverse("confirmar-entrega", kwargs={"item_id": self.item.id})

    def test_confirmar_entrega_exitoso_cambia_a_entregado_y_notifica(self):
        self.client.force_authenticate(user=self.vendedor)
        payload = {"codigo": "987654"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("mensaje", response.data)

        self.item.refresh_from_db()
        self.assertEqual(self.item.estado_entrega, ItemPedido.EstadoEntrega.ENTREGADO)

        # Notificación al vendedor: fondos liberados
        notif_vendedor = Notificacion.objects.filter(usuario=self.vendedor, tipo="PEDIDO").latest("creado_el")
        self.assertIn("fondos", notif_vendedor.titulo.lower() + notif_vendedor.mensaje.lower())

        # Notificación al comprador: entrega completada
        notif_comprador = Notificacion.objects.filter(usuario=self.comprador, tipo="PEDIDO").latest("creado_el")
        self.assertIn("entrega", notif_comprador.titulo.lower() + notif_comprador.mensaje.lower())

    def test_confirmar_entrega_con_clave_codigo_secreto(self):
        """Acepta también 'codigo_secreto' como clave en el payload."""
        self.client.force_authenticate(user=self.vendedor)
        payload = {"codigo_secreto": "987654"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.estado_entrega, ItemPedido.EstadoEntrega.ENTREGADO)

    def test_confirmar_entrega_codigo_incorrecto_devuelve_400(self):
        self.client.force_authenticate(user=self.vendedor)
        payload = {"codigo": "111111"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.item.refresh_from_db()
        self.assertEqual(self.item.estado_entrega, ItemPedido.EstadoEntrega.EN_CUSTODIA)

    def test_confirmar_entrega_sin_codigo_devuelve_400(self):
        self.client.force_authenticate(user=self.vendedor)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_solo_vendedor_puede_confirmar_comprador_y_ajenos_reciben_403(self):
        # El comprador tiene el código, pero NO puede auto-confirmarse la entrega
        self.client.force_authenticate(user=self.comprador)
        resp_comprador = self.client.post(self.url, {"codigo": "987654"}, format="json")
        self.assertEqual(resp_comprador.status_code, status.HTTP_403_FORBIDDEN)

        # Un usuario ajeno tampoco puede
        self.client.force_authenticate(user=self.ajeno)
        resp_ajeno = self.client.post(self.url, {"codigo": "987654"}, format="json")
        self.assertEqual(resp_ajeno.status_code, status.HTTP_403_FORBIDDEN)

        self.item.refresh_from_db()
        self.assertEqual(self.item.estado_entrega, ItemPedido.EstadoEntrega.EN_CUSTODIA)

    def test_confirmar_entrega_dos_veces_devuelve_400(self):
        self.client.force_authenticate(user=self.vendedor)

        primera = self.client.post(self.url, {"codigo": "987654"}, format="json")
        self.assertEqual(primera.status_code, status.HTTP_200_OK)

        segunda = self.client.post(self.url, {"codigo": "987654"}, format="json")
        self.assertEqual(segunda.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirmar_entrega_item_inexistente_devuelve_404(self):
        self.client.force_authenticate(user=self.vendedor)
        url_inexistente = reverse("confirmar-entrega", kwargs={"item_id": 999999})

        response = self.client.post(url_inexistente, {"codigo": "987654"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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


class ModeracionProductoTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin-moderacion@repilche.com",
            password="PasswordSegura123!",
            first_name="Admin",
            last_name="Moderación",
            is_staff=True,
        )
        self.usuario = User.objects.create_user(
            email="vendedor-moderacion@repilche.com",
            password="PasswordSegura123!",
            first_name="Vendedor",
            last_name="Prueba",
            is_vendedor=True,
        )
        self.categoria = Categoria.objects.create(nombre="Moderación")
        self.producto = Producto.objects.create(
            vendedor=self.usuario,
            categoria=self.categoria,
            nombre="Campera pendiente",
            descripcion="Campera vintage",
            precio=25000,
            stock=1,
        )
        self.list_url = reverse("moderation-product-list")
        self.approve_url = reverse(
            "moderation-product-approve",
            args=[self.producto.id],
        )
        self.reject_url = reverse(
            "moderation-product-reject",
            args=[self.producto.id],
        )

    def test_usuario_comun_recibe_403_y_sin_token_401(self):
        response_sin_token = self.client.get(self.list_url)
        self.client.force_authenticate(user=self.usuario)
        response_usuario = self.client.get(self.list_url)

        self.assertEqual(response_sin_token.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response_usuario.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_lista_solo_productos_pendientes_en_orden_ascendente(self):
        producto_anterior = Producto.objects.create(
            vendedor=self.usuario,
            categoria=self.categoria,
            nombre="Pendiente anterior",
            descripcion="Más antiguo",
            precio=20000,
            stock=1,
        )
        producto_aprobado = Producto.objects.create(
            vendedor=self.usuario,
            categoria=self.categoria,
            nombre="Producto aprobado",
            descripcion="No debe aparecer",
            precio=15000,
            stock=1,
            estado_moderacion="APROBADO",
        )
        Producto.objects.filter(pk=producto_anterior.pk).update(
            creado_el=self.producto.creado_el.replace(year=2020)
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertEqual(
            [item["id"] for item in data],
            [producto_anterior.id, self.producto.id],
        )
        self.assertNotIn(producto_aprobado.id, [item["id"] for item in data])

    def test_approve_aprueba_y_notifica_al_vendedor(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(self.approve_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.estado_moderacion, "APROBADO")
        self.assertIsNotNone(self.producto.moderado_el)
        self.assertEqual(self.producto.motivo_rechazo, "")
        notificacion = Notificacion.objects.get(usuario=self.usuario)
        self.assertEqual(notificacion.tipo, "MODERACION")
        self.assertIn("ya está publicada", notificacion.mensaje)
        self.assertEqual(response.data["estado_moderacion"], "APROBADO")

    def test_reject_sin_motivo_devuelve_400_sin_cambiar_producto(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(self.reject_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("motivo", response.data)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.estado_moderacion, "PENDIENTE")
        self.assertEqual(self.producto.motivo_rechazo, "")
        self.assertIsNone(self.producto.moderado_el)
        self.assertFalse(Notificacion.objects.exists())

    def test_reject_guarda_motivo_y_notifica_al_vendedor(self):
        self.client.force_authenticate(user=self.admin)
        motivo = "La descripción no coincide con las fotos."

        response = self.client.post(
            self.reject_url,
            {"motivo": motivo},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.estado_moderacion, "RECHAZADO")
        self.assertEqual(self.producto.motivo_rechazo, motivo)
        self.assertIsNotNone(self.producto.moderado_el)
        notificacion = Notificacion.objects.get(usuario=self.usuario)
        self.assertEqual(notificacion.tipo, "MODERACION")
        self.assertIn(motivo, notificacion.mensaje)
        self.assertEqual(response.data["motivo_rechazo"], motivo)

    def test_approve_dos_veces_devuelve_400(self):
        self.client.force_authenticate(user=self.admin)
        primera_respuesta = self.client.post(self.approve_url)
        segunda_respuesta = self.client.post(self.approve_url)

        self.assertEqual(primera_respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(segunda_respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Notificacion.objects.filter(usuario=self.usuario).count(), 1)

    def test_producto_aprobado_aparece_en_catalogo_publico(self):
        self.client.force_authenticate(user=self.admin)

        self.client.post(self.approve_url)
        response = self.client.get(reverse("product-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertIn(self.producto.id, [item["id"] for item in data])