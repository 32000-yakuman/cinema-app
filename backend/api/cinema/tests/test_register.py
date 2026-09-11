from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from api.cinema.models import UserPoint, PointTransaction

User = get_user_model()


class RegisterViewTests(TestCase):
    """
    RegisterView(会員登録API)のテスト。
    RegisterSerializerが持つ3つのバリデーション
    (ユーザー名重複・パスワード強度・姓名は任意入力)を中心に確認する。
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/cinema/register/"

    def test_register_success_creates_user(self):
        """正しい入力で登録でき、パスワードはハッシュ化されて保存されること"""
        response = self.client.post(
            self.url,
            {"username": "new-user", "password": "correct-horse-battery-staple",
             "first_name": "太郎", "last_name": "山田"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="new-user")
        self.assertEqual(user.first_name, "太郎")
        # create_user()経由なので平文のままDBに残っていないこと
        self.assertNotEqual(user.password, "correct-horse-battery-staple")
        self.assertTrue(user.check_password("correct-horse-battery-staple"))

    def test_register_without_name_succeeds(self):
        """姓名は任意入力のため、未指定でも登録できること"""
        response = self.client.post(
            self.url,
            {"username": "no-name-user", "password": "correct-horse-battery-staple"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_duplicate_username_returns_400(self):
        """既に使われているユーザー名では登録できないこと"""
        User.objects.create_user(username="taken-user", password="whatever-password")
        response = self.client.post(
            self.url,
            {"username": "taken-user", "password": "correct-horse-battery-staple"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertEqual(User.objects.filter(username="taken-user").count(), 1)

    def test_register_too_short_password_returns_400(self):
        """MinimumLengthValidator(既定8文字)未満は400、ユーザーも作られないこと"""
        response = self.client.post(
            self.url, {"username": "short-pass-user", "password": "abc123"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="short-pass-user").exists())

    def test_register_password_similar_to_username_returns_400(self):
        """UserAttributeSimilarityValidatorにより、ユーザー名と酷似したパスワードは400"""
        response = self.client.post(
            self.url,
            {"username": "similar-user-name", "password": "similar-user-name"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_numeric_only_password_returns_400(self):
        """NumericPasswordValidatorにより、数字のみのパスワードは400"""
        response = self.client.post(
            self.url, {"username": "numeric-pass-user", "password": "48291673"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_common_password_returns_400(self):
        """CommonPasswordValidatorにより、よくあるパスワードは400"""
        response = self.client.post(
            self.url, {"username": "common-pass-user", "password": "password1"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_username_returns_400(self):
        """usernameが未指定だと400になること"""
        response = self.client.post(
            self.url, {"password": "correct-horse-battery-staple"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_register_success_grants_signup_bonus_points(self):
        """登録成功時にUserPointが作成され、5ptが付与されること。
        あわせてPointTransactionにも付与履歴(EARN, +5)が1件残ること"""
        response = self.client.post(
            self.url,
            {"username": "bonus-user", "password": "correct-horse-battery-staple"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="bonus-user")

        user_point = UserPoint.objects.get(user=user)
        self.assertEqual(user_point.balance, 5)

        transactions = PointTransaction.objects.filter(user=user)
        self.assertEqual(transactions.count(), 1)
        transaction = transactions.first()
        self.assertEqual(transaction.type, PointTransaction.Type.EARN)
        self.assertEqual(transaction.amount, 5)
        self.assertIsNone(transaction.reservation)

def test_register_failure_does_not_create_user_point(self):
    """登録が400で失敗した場合、UserPointも作られないこと
    (transaction.atomicでUser作成とポイント付与が一体になっていることの確認)"""
    User.objects.create_user(username="taken-user", password="whatever-password")

    response = self.client.post(
        self.url,
        {"username": "taken-user", "password": "correct-horse-battery-staple"},
        format="json",
    )
    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertFalse(UserPoint.objects.filter(user__username="taken-user").exists())