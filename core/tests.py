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
