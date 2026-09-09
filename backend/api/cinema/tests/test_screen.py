from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from api.cinema.models import (
    Theater, Screen, Seat
)

User = get_user_model()

class ScreenCreateTests(TestCase):
    """
    ScreenSerializerの座席数バリデーションに関する回帰テスト。

    以前はrow_countのチェックがScreen保存後(_generate_seats内)で
    行われていたため、27行以上を指定してバリデーションエラーになっても
    座席の無い壊れたScreenレコードがDBに残ってしまうバグがあった。
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="admin-user", password="test-password", is_staff=True
        )
        self.theater = Theater.objects.create(name="テスト劇場", address="テスト住所")

    def test_row_count_over_26_does_not_create_orphan_screen(self):
        """
        row_countが26を超える場合は400になり、Screenレコード自体が
        作成されないこと(座席の無いScreenが残らないこと)
        """
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/api/cinema/screens/",
            {
                "theater": self.theater.id,
                "name": "巨大スクリーン",
                "row_count": 27,
                "col_count": 10,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Screen自体が作られていないこと(以前のバグでは壊れたレコードが残っていた)
        self.assertEqual(Screen.objects.count(), 0)

    def test_row_count_26_creates_seats_correctly(self):
        """
        row_countが26(境界値)なら正常に作成され、座席も生成されること
        """
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/api/cinema/screens/",
            {
                "theater": self.theater.id,
                "name": "標準スクリーン",
                "row_count": 26,
                "col_count": 10,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        screen = Screen.objects.get()
        self.assertEqual(Seat.objects.filter(screen=screen).count(), 26 * 10)


