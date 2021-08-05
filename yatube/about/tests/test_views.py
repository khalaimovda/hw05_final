from django.shortcuts import reverse
from django.test import Client, TestCase
from http import HTTPStatus


class ViewTests(TestCase):
    """View-функции работают корректно."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.url_template_map = {
            reverse("about:author"): "about/author.html",
            reverse("about:tech"): "about/tech.html",
        }

    def setUp(self):
        self.client = Client()

    def test_url_accessibility(self):
        """Страницы доступны по соответствующему URL."""
        for url in ViewTests.url_template_map.keys():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in ViewTests.url_template_map.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, template)
