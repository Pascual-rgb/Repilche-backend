from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

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
