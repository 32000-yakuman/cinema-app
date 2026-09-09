from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

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
            "/api/cinema/login/",
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
            "/api/cinema/login/",
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
        response = self.client.get("/api/cinema/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_login_returns_user_info(self):
        """
        ログイン後に/meにアクセスするとユーザー情報が返る
        """
        login_response = self.client.post(
            "/api/cinema/login/",
            {
                "username" :self.username,
                "password" :self.password
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        me_response = self.client.get("/api/cinema/me/")
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data.get("user_id"), self.user.id)

    def test_reservations_requires_authentication(self):
        """
        未ログイン状態で予約一覧を呼ぶと401が返る
        """
        request = self.client.get("/api/cinema/reservations/")

        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)