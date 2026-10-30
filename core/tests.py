from django.test import TestCase
from django.urls import reverse
from django.contrib import admin
from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthAndUserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("registro")
        self.login_url = reverse("login")
        self.me_url = reverse("usuario-me")
        self.vendedor_url = reverse("ser-vendedor")

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

    def test_registro_falla_con_telefono_no_numerico(self):
        """El backend debe rechazar teléfonos con letras o caracteres no numéricos."""
        payload = {
            "name": "Martin",
            "lastName": "Gomez",
            "numberPhone": "2804-ABC-123",
            "email": "tel_invalido@repilche.com",
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
        self.assertEqual(get_res.data["nombre"], "Ezequiel")
        self.assertEqual(get_res.data["apellido"], "Martinez")
        self.assertEqual(get_res.data["first_name"], "Ezequiel")
        self.assertEqual(get_res.data["last_name"], "Martinez")

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

    def test_ser_vendedor_con_alias_bancario_y_lista_localidades(self):
        """Permite enviar alias_bancario y una lista de zonas/ciudades de entrega."""
        user = User.objects.create_user(
            email="vendedor_alias@repilche.com",
            password="Password123!",
            first_name="Vendedora",
        )
        self.client.force_authenticate(user=user)

        payload = {
            "locality": "Gaiman",
            "llegoHasta": ["Trelew", "Rawson", "Playa Unión"],
            "alias_bancario": "MARCOS.ROPA.VINTAGE",
            "description": "Ropa seleccionada.",
        }
        response = self.client.post(self.vendedor_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user.refresh_from_db()
        self.assertTrue(user.is_vendedor)
        self.assertEqual(user.perfil_vendedor.localidad, "Gaiman")
        self.assertEqual(user.perfil_vendedor.llego_hasta, "Trelew, Rawson, Playa Unión")
        self.assertEqual(user.perfil_vendedor.cvu, "MARCOS.ROPA.VINTAGE")

    def test_usuario_creado_desde_formulario_admin_puede_iniciar_sesion(self):
        admin_form = admin.site._registry[User].get_form(
            RequestFactory().get("/admin/core/customuser/add/")
        )
        form = admin_form(
            data={
                "email": "creado-admin@repilche.com",
                "first_name": "Usuario",
                "last_name": "Admin",
                "phone": "2804123456",
                "password1": "PasswordAdmin123!",
                "password2": "PasswordAdmin123!",
                "is_vendedor": False,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.has_usable_password())

        response = self.client.post(
            self.login_url,
            {
                "email": user.email,
                "password": "PasswordAdmin123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
    def test_ser_vendedor_con_payload_frontend_camelcase_y_alias(self):
        """Prueba envío con payload exacto del frontend (locality, llegoHasta, alias, description)."""
        user = User.objects.create_user(
            email="vendedor_frontend@repilche.com",
            password="Password123!",
            first_name="Frontend",
        )
        self.client.force_authenticate(user=user)

        payload = {
            "locality": "Rawson",
            "llegoHasta": "Rawson",
            "alias": "wertwer",
            "description": "werywteywët",
        }
        response = self.client.post(self.vendedor_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_vendedor"])

        user.refresh_from_db()
        self.assertTrue(user.is_vendedor)
        self.assertEqual(user.perfil_vendedor.localidad, "Rawson")
        self.assertEqual(user.perfil_vendedor.llego_hasta, "Rawson")
        self.assertEqual(user.perfil_vendedor.cvu, "wertwer")
        self.assertEqual(user.perfil_vendedor.descripcion, "werywteywët")

    def test_ser_vendedor_update_or_create_no_colisiona_si_ya_existe(self):
        """Verifica que update_or_create actualice el perfil si ya existe sin dar IntegrityError 500."""
        user = User.objects.create_user(
            email="vendedor_duplicado@repilche.com",
            password="Password123!",
            first_name="Duplicado",
        )
        self.client.force_authenticate(user=user)

        payload_inicial = {
            "locality": "Rawson",
            "llegoHasta": "Rawson",
            "alias": "alias.inicial",
            "description": "Desc inicial",
        }
        res1 = self.client.post(self.vendedor_url, payload_inicial, format="json")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        payload_actualizado = {
            "locality": "Playa Unión",
            "llegoHasta": "Rawson y Trelew",
            "alias": "alias.actualizado",
            "description": "Desc actualizada",
        }
        res2 = self.client.post(self.vendedor_url, payload_actualizado, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.is_vendedor)
        self.assertEqual(user.perfil_vendedor.localidad, "Playa Unión")
        self.assertEqual(user.perfil_vendedor.cvu, "alias.actualizado")
        self.assertEqual(user.perfil_vendedor.descripcion, "Desc actualizada")

    def test_ser_vendedor_sin_descripcion_usa_default_seguro(self):
        """Verifica que no falle con 500 cuando no se envía description."""
        user = User.objects.create_user(
            email="vendedor_sin_desc@repilche.com",
            password="Password123!",
            first_name="SinDesc",
        )
        self.client.force_authenticate(user=user)

        payload = {
            "locality": "Trelew",
            "llegoHasta": "Trelew",
            "alias": "alias.sindesc",
        }
        response = self.client.post(self.vendedor_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user.refresh_from_db()
        self.assertEqual(user.perfil_vendedor.descripcion, "")

    def test_ser_vendedor_error_400_con_datos_invalidos(self):
        """Verifica que datos inválidos devuelvan 400 y no 500."""
        user = User.objects.create_user(
            email="vendedor_invalido@repilche.com",
            password="Password123!",
            first_name="Invalido",
        )
        self.client.force_authenticate(user=user)

        # Sin localidad ni zona de entrega ni alias
        response = self.client.post(self.vendedor_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProductSerializerTests(TestCase):
    def setUp(self):
        from Repilche.models import Categoria
        self.vendedor = User.objects.create_user(
            email="vendedor_producto@repilche.com",
            password="Password123!",
            first_name="Vendedor",
            is_vendedor=True,
        )
        self.categoria = Categoria.objects.create(nombre="Buzos", slug="buzos")
        self.factory = RequestFactory()

    def test_creacion_producto_con_imagen_url_normaliza_y_persiste(self):
        from api.serializers import ProductSerializer
        supabase_url = "https://xyz.supabase.co/storage/v1/object/public/productos/buzo-test.webp"
        request = self.factory.post("/api/products/")
        request.user = self.vendedor

        serializer = ProductSerializer(
            data={
                "categoria": self.categoria.id,
                "nombre": "Buzo Oversize",
                "descripcion": "Buzo vintage talle L",
                "precio": "15000.00",
                "imagen_url": supabase_url,
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        producto = serializer.save()

        self.assertEqual(producto.imagen, supabase_url)
        # Salida serializada para el frontend
        data = ProductSerializer(producto).data
        self.assertEqual(data["imagen"], supabase_url)
        self.assertEqual(data["imagen_url"], supabase_url)
        self.assertEqual(data["img"], supabase_url)

    def test_creacion_producto_con_img_normaliza_y_persiste(self):
        from api.serializers import ProductSerializer
        supabase_url = "https://xyz.supabase.co/storage/v1/object/public/productos/remera.webp"
        request = self.factory.post("/api/products/")
        request.user = self.vendedor

        serializer = ProductSerializer(
            data={
                "categoria": self.categoria.id,
                "nombre": "Remera Retro",
                "descripcion": "Remera algodón",
                "precio": "8000.00",
                "img": supabase_url,
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        producto = serializer.save()

        self.assertEqual(producto.imagen, supabase_url)
        data = ProductSerializer(producto).data
        self.assertEqual(data["imagen_url"], supabase_url)

    def test_producto_serializer_con_tres_urls_concatenadas(self):
        """Auditoría: ProductoSerializer acepta hasta 3 URLs concatenadas por coma sin fallar por URLField."""
        from api.serializers import ProductoSerializer
        multi_urls = "https://cdn.repilche.com/1.png,https://cdn.repilche.com/2.png,https://cdn.repilche.com/3.png"
        request = self.factory.post("/api/products/")
        request.user = self.vendedor

        serializer = ProductoSerializer(
            data={
                "categoria": self.categoria.id,
                "nombre": "Pantalón Cargo",
                "descripcion": "Verde oliva",
                "precio": "25000.00",
                "imagen": multi_urls,
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        producto = serializer.save()

        self.assertEqual(producto.imagen, multi_urls)
        data = ProductoSerializer(producto).data
        self.assertEqual(data["imagen"], multi_urls)
        self.assertEqual(data["imagen_url"], multi_urls)
        self.assertEqual(data["img"], multi_urls)

    def test_producto_serializer_expone_vendedor_nombre_real(self):
        """Verifica que ProductSerializer exponga vendedor_nombre con nombre y apellido."""
        from api.serializers import ProductSerializer
        from Repilche.models import Producto
        self.vendedor.first_name = "Valentino"
        self.vendedor.last_name = "Rossi"
        self.vendedor.save()

        producto = Producto.objects.create(
            vendedor=self.vendedor,
            categoria=self.categoria,
            nombre="Gorra Racing",
            descripcion="Vintage",
            precio=12000.00,
        )
        data = ProductSerializer(producto).data
        self.assertIn("vendedor_nombre", data)
        self.assertEqual(data["vendedor_nombre"], "Valentino Rossi")

        # Fallback al prefijo de email si no tiene nombre
        self.vendedor.first_name = ""
        self.vendedor.last_name = ""
        self.vendedor.email = "rossi@repilche.com"
        self.vendedor.save()
        data_fallback = ProductSerializer(producto).data
        self.assertEqual(data_fallback["vendedor_nombre"], "rossi")




class PedidoCheckoutC2CTests(TestCase):
    def setUp(self):
        from Repilche.models import Categoria, Producto, Pedido, ItemPedido
        self.client = APIClient()
        self.pedidos_url = reverse("pedido-list")
        self.pedidos_crear_url = reverse("pedido-crear")

        self.categoria = Categoria.objects.create(nombre="Gorras", slug="gorras")
        self.vendedor = User.objects.create_user(
            email="vendedor_c2c_checkout@repilche.com",
            password="Password123!",
            first_name="Marcos",
            is_vendedor=True,
        )
        self.comprador = User.objects.create_user(
            email="comprador_c2c_checkout@repilche.com",
            password="Password123!",
            first_name="Florencia",
        )
        self.producto = Producto.objects.create(
            vendedor=self.vendedor,
            categoria=self.categoria,
            nombre="Gorra Vintage",
            descripcion="Gorra en excelente estado",
            precio=15000.00,
            stock=1,
            estado=Producto.Estado.DISPONIBLE,
            estado_moderacion=Producto.EstadoModeracion.APROBADO,
        )

    def test_checkout_requiere_autenticacion(self):
        response = self.client.post(self.pedidos_url, {"producto_id": self.producto.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_compra_directa_exitosa(self):
        from Repilche.models import Producto, Pedido, ItemPedido
        self.client.force_authenticate(user=self.comprador)
        response = self.client.post(self.pedidos_url, {"producto_id": self.producto.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data
        self.assertIn("id", data)
        self.assertEqual(data["mensaje"], "Compra realizada con éxito")
        self.assertEqual(data["producto"]["id"], self.producto.id)
        self.assertEqual(data["producto"]["nombre"], "Gorra Vintage")
        self.assertEqual(data["total"], 15000.00)
        self.assertIn("codigo_secreto", data)
        self.assertEqual(len(data["codigo_secreto"]), 6)
        self.assertEqual(data["alias_transferencia"], "repilche")
        self.assertEqual(data["titular"], "Maia Hernandez")
        self.assertNotIn("cbu_cvu", data)
        self.assertEqual(data["estado"], "PENDIENTE")

        # Verificar que el producto quedó VENDIDO y stock 0
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.estado, Producto.Estado.VENDIDO)
        self.assertEqual(self.producto.stock, 0)
        self.assertFalse(self.producto.activo)

        # Verificar Pedido e ItemPedido en BD
        pedido = Pedido.objects.get(id=data["id"])
        self.assertEqual(pedido.comprador, self.comprador)
        self.assertEqual(pedido.total, 15000.00)
        self.assertEqual(self.comprador.compras.count(), 1)
        self.assertEqual(self.vendedor.ventas_items.count(), 1)

        # Verificar que el producto comprado ya NO aparece en el catálogo público
        catalogo_resp = self.client.get(reverse("product-list"))
        results = catalogo_resp.data.get("results", catalogo_resp.data)
        ids_en_catalogo = [p["id"] for p in results]
        self.assertNotIn(self.producto.id, ids_en_catalogo)

    def test_compra_directa_alias_url_pedidos_crear(self):
        self.client.force_authenticate(user=self.comprador)
        response = self.client.post(self.pedidos_crear_url, {"producto_id": self.producto.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_error_producto_no_disponible(self):
        from Repilche.models import Producto
        self.producto.estado = Producto.Estado.VENDIDO
        self.producto.stock = 0
        self.producto.save()

        self.client.force_authenticate(user=self.comprador)
        response = self.client.post(self.pedidos_url, {"producto_id": self.producto.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("error"), "El producto ya no está disponible")

    def test_error_vendedor_no_puede_comprar_su_propia_prenda(self):
        self.client.force_authenticate(user=self.vendedor)
        response = self.client.post(self.pedidos_url, {"producto_id": self.producto.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("error"), "Un vendedor no puede comprar su propia prenda.")

    def test_historial_compras_incluye_desglose_exacto_items(self):
        # 1. Realizar compra exitosa
        self.client.force_authenticate(user=self.comprador)
        post_resp = self.client.post(self.pedidos_url, {"producto_id": self.producto.id}, format="json")
        self.assertEqual(post_resp.status_code, status.HTTP_201_CREATED)

        # 2. Consultar GET /api/pedidos/
        get_resp = self.client.get(self.pedidos_url)
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)
        results = get_resp.data.get("results", get_resp.data)
        self.assertGreaterEqual(len(results), 1)

        pedido_data = results[0]
        self.assertIn("pedido_id", pedido_data)
        self.assertIn("fecha", pedido_data)
        self.assertEqual(pedido_data["total"], 15000.00)
        self.assertEqual(pedido_data["estado"], "PENDIENTE")
        self.assertIn("items", pedido_data)
        self.assertEqual(len(pedido_data["items"]), 1)

        item = pedido_data["items"][0]
        self.assertIn("item_id", item)
        self.assertEqual(item["producto_id"], self.producto.id)
        self.assertEqual(item["nombre"], "Gorra Vintage")
        self.assertEqual(item["precio"], 15000.00)
        self.assertEqual(item["vendedor_id"], self.vendedor.id)
        self.assertEqual(item["vendedor_nombre"], "Marcos")
        self.assertEqual(len(item["codigo_secreto"]), 6)
        self.assertEqual(item["estado_entrega"], "en_custodia")

        # 3. Consultar GET /api/mis-compras/?agrupado=true
        mis_compras_resp = self.client.get(reverse("mis-compras") + "?agrupado=true")
        self.assertEqual(mis_compras_resp.status_code, status.HTTP_200_OK)
        mc_results = mis_compras_resp.data.get("results", mis_compras_resp.data)
        self.assertGreaterEqual(len(mc_results), 1)
        self.assertEqual(mc_results[0]["pedido_id"], pedido_data["pedido_id"])
