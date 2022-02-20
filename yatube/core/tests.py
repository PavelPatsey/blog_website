from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        """Тест обработки ошибки 404: если страница не найдена, то
        сервер возвращает код 404;
        при ошибке 404 используется кастомный шаблон."""
        response = self.client.get("/nonexist-page/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "core/404.html")
