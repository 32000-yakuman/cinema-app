from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

# Create your tests here.
class AuthFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = "test-user"
        self.password = "test-password"
        self.user = User.objects.create_user(
            username=self.username, password=self.password
        )

    def test_login_success(self):
        """
        正しい認証情報でログインできる
        """
        response = self.client.post(
            "/api/inventory/login/",
            {
                "username": self.username,
                "password": self.password
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)

    def test_login_failure_wrong_pass(self):
        """
        誤ったパスワードで401エラーが返る
        """
        response = self.client.post(
            "/api/inventory/login/",
            {
                "username" :self.username,
                "password" :"wrong.password"
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_me_without_login_returns_401(self):
        """
        ログインしていない状態で/meにアクセスすると401が返る
        """
        response = self.client.get("/api/inventory/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_login_returns_user_info(self):
        """
        ログイン後に/meにアクセスするとユーザー情報が返る
        """
        login_response = self.client.post(
            "/api/inventory/login/",
            {
                "username" :self.username,
                "password" :self.password
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        me_response = self.client.get("/api/inventory/me/")
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data.get("user_id"), self.user.id)

    def test_products_requires_authentication(self):
        """
        未ログイン状態で商品一覧を呼ぶと401が返る
        """
        request = self.client.get("/api/inventory/products/")

        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)