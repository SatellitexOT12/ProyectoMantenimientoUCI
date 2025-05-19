from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from django.contrib.auth.models import User

class LoginPageTest(LiveServerTestCase):

        @classmethod
        def setUpClass(cls):
                super().setUpClass()
                # Configurar Firefox en modo headless (opcional)
                firefox_options = Options()
                #firefox_options.add_argument('--headless')
                cls.browser = webdriver.Firefox(options=firefox_options)

        @classmethod
        def tearDownClass(cls):
                cls.browser.quit()
                super().tearDownClass()

        def setUp(self):
                # Crear un usuario de prueba
                self.user = User.objects.create_user(username='testuser', password='12345')

        def test_page_loads_correctly(self):
                """Verifica que la página carga correctamente"""
                self.browser.get(self.live_server_url)
        
                # Verificar título
                WebDriverWait(self.browser, 10).until(
                        EC.title_contains("Login")
                )
                self.assertIn("Login", self.browser.title)

                # Verificar URL
                self.assertEqual(self.browser.current_url, self.live_server_url + "/")

        def test_welcome_text_displayed(self):
                """Verifica que los textos de bienvenida están visibles"""
                self.browser.get(self.live_server_url)

                # Verificar "Bienvenido"
                h1 = WebDriverWait(self.browser, 10).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, "text-prest"))
                )
                self.assertEqual(h1.text, "Bienvenido")

                # Verificar descripción
                h2 = self.browser.find_element(By.CLASS_NAME, "text-sub")
                self.assertEqual(h2.text, "Sistema de mantenimiento de la Universidad de Ciencias Informaticas")

        def test_form_fields_present_and_required(self):
                """Verifica que los campos del formulario existen y son obligatorios"""
                self.browser.get(self.live_server_url)

                # Usuario
                username = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.NAME, "username"))
                )
                self.assertTrue(username.is_displayed())
                self.assertTrue(username.get_attribute("required"))

                # Contraseña
                password = self.browser.find_element(By.NAME, "password")
                self.assertTrue(password.is_displayed())
                self.assertTrue(password.get_attribute("required"))

        def test_form_validation_on_empty_submit(self):
                """Verifica que los mensajes de validación aparecen al enviar el formulario vacío"""
                self.browser.get(self.live_server_url)

                # Esperar a que el botón de submit sea clickeable y hacer clic
                submit_button = WebDriverWait(self.browser, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
                )
                submit_button.click()

                # Localizar el campo de usuario
                username = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.NAME, "username"))
                )

                # Usar JavaScript para obtener el objeto validity
                validity = self.browser.execute_script(
                "return arguments[0].validity;", username
                )

                # Verificar que el campo es inválido
                self.assertFalse(validity["valid"])

                # Verificar que el mensaje de error se muestra
                invalid_feedback = WebDriverWait(self.browser, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//div[contains(text(), "Por favor llena este campo")]'))
                )
                self.assertTrue(invalid_feedback.is_displayed())

        def test_password_toggle_visibility(self):
                """Verifica que el botón de mostrar contraseña funciona"""
                self.browser.get(self.live_server_url)

                # Obtener elementos
                pwd_input = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.ID, "password"))
                )
                toggle_btn = self.browser.find_element(By.ID, "togglePassword")

                # Inicialmente debe ser tipo 'password'
                self.assertEqual(pwd_input.get_attribute("type"), "password")

                # Hacer clic para mostrar
                toggle_btn.click()
                WebDriverWait(self.browser, 10).until(
                        lambda driver: pwd_input.get_attribute("type") == "text"
                )
                self.assertEqual(pwd_input.get_attribute("type"), "text")

                # Hacer clic otra vez para ocultar
                toggle_btn.click()
                WebDriverWait(self.browser, 10).until(
                        lambda driver: pwd_input.get_attribute("type") == "password"
                )
                self.assertEqual(pwd_input.get_attribute("type"), "password")

        def test_login_with_invalid_credentials(self):
                """Verifica que se muestra un mensaje de error al usar credenciales incorrectas"""
                self.browser.get(self.live_server_url)

                # Llenar formulario con credenciales incorrectas
                username = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.NAME, "username"))
                )
                username.send_keys("usuario_invalido")

                password = self.browser.find_element(By.NAME, "password")
                password.send_keys("clave_invalida")

                submit = self.browser.find_element(By.XPATH, '//button[@type="submit"]')
                submit.click()

                # Esperar mensaje de error
                error_div = WebDriverWait(self.browser, 10).until(
                        EC.visibility_of_element_located((By.XPATH, '//div[@class="err"]'))
                )
                self.assertTrue(error_div.is_displayed())
                self.assertIn("Credenciales inválidas", error_div.text)

        def test_login_with_valid_credentials(self):
                """Verifica que el login exitoso redirige a otra página"""
                self.browser.get(self.live_server_url)

                # Llenar formulario con credenciales válidas
                username = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.NAME, "username"))
                )
                username.send_keys("testuser")

                password = self.browser.find_element(By.NAME, "password")
                password.send_keys("12345")

                submit = self.browser.find_element(By.XPATH, '//button[@type="submit"]')
                submit.click()

                # Esperar redirección (ajusta la URL según tu app)
                WebDriverWait(self.browser, 10).until(
                        EC.url_contains("main")  # Cambia "dashboard" por tu URL real
                )
                self.assertIn("main", self.browser.current_url.lower())