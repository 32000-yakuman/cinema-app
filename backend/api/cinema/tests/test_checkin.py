import uuid
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from api.cinema.models import (
    Theater, Screen, Movie, Showtime, 
    Reservation, Payment, UserPoint,
)

User = get_user_model()

class CheckInByTokenTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.staff_user = User.objects.create_user(
            username="staff-user", password="test-password", is_staff_member=True
        )
        self.customer = User.objects.create_user(
            username="customer-user", password="test-password"
        )

        theater = Theater.objects.create(name="テスト劇場", address="テスト住所")
        screen = Screen.objects.create(
            theater=theater, name="スクリーン1", row_count=5, col_count=5
        )
        movie = Movie.objects.create(
            title="テスト映画", duration_minutes=120,
            release_date=timezone.now().date(),
        )
        self.showtime = Showtime.objects.create(
            movie=movie, screen=screen,
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=3),
            base_price=1500,
        )

    def _create_reservation(self, payment_status=None, checked_in_at=None):
        reservation = Reservation.objects.create(
            user=self.customer,
            showtime=self.showtime,
            total_price=1500,
            status=Reservation.Status.CONFIRMED,
            checked_in_at=checked_in_at,
        )
        if payment_status is not None:
            Payment.objects.create(
                reservation=reservation,
                amount=1500,
                method=Payment.Method.CASH,
                status=payment_status,
            )
        return reservation

    def test_checkin_by_token_success(self):
        """
        窓口職員が有効なtokenでチェックインできる
        """
        reservation = self._create_reservation(payment_status=Payment.Status.CONFIRMED)
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            "/api/cinema/staff/checkin-by-token/",
            {"token": str(reservation.checkin_token)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertIsNotNone(reservation.checked_in_at)

        user_point = UserPoint.objects.get(user=self.customer)
        self.assertGreater(user_point.balance, 0)

    def test_checkin_by_token_requires_staff(self):
        """
        窓口職員でないユーザーは403になる
        """
        reservation = self._create_reservation(payment_status=Payment.Status.CONFIRMED)
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            "/api/cinema/staff/checkin-by-token/",
            {"token": str(reservation.checkin_token)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_checkin_by_token_requires_authentication(self):
        """
        未ログインだと401になる
        """
        reservation = self._create_reservation(payment_status=Payment.Status.CONFIRMED)

        response = self.client.post(
            "/api/cinema/staff/checkin-by-token/",
            {"token": str(reservation.checkin_token)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_checkin_by_token_missing_token_returns_400(self):
        """
        tokenが未指定だと400になる
        """
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            "/api/cinema/staff/checkin-by-token/", {}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkin_by_token_unknown_token_returns_404(self):
        """
        存在しないtokenは404になる
        """
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            "/api/cinema/staff/checkin-by-token/",
            {"token": str(uuid.uuid4())},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_checkin_by_token_unconfirmed_payment_returns_400(self):
        """
        決済未確定の予約はチェックインできない
        """
        reservation = self._create_reservation(payment_status=Payment.Status.PENDING)
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            "/api/cinema/staff/checkin-by-token/",
            {"token": str(reservation.checkin_token)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkin_by_token_already_checked_in_returns_400(self):
        """
        すでにチェックイン済みの予約は再チェックインできない
        """
        reservation = self._create_reservation(
            payment_status=Payment.Status.CONFIRMED,
            checked_in_at=timezone.now(),
        )
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            "/api/cinema/staff/checkin-by-token/",
            {"token": str(reservation.checkin_token)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reservation_detail_hides_token_when_unconfirmed(self):
        """
        決済未確定の予約詳細ではcheckin_tokenがnullで返る
        """
        reservation = self._create_reservation(payment_status=Payment.Status.PENDING)
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(f"/api/cinema/reservations/{reservation.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data.get("checkin_token"))

    def test_reservation_detail_shows_token_when_confirmed(self):
        """
        決済確定済み・未チェックインの予約詳細ではcheckin_tokenが返る
        """
        reservation = self._create_reservation(payment_status=Payment.Status.CONFIRMED)
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(f"/api/cinema/reservations/{reservation.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("checkin_token"), str(reservation.checkin_token))

    def test_reservation_detail_hides_token_when_already_checked_in(self):
        """
        チェックイン済みの予約詳細ではcheckin_tokenがnullで返る
        """
        reservation = self._create_reservation(
            payment_status=Payment.Status.CONFIRMED,
            checked_in_at=timezone.now(),
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(f"/api/cinema/reservations/{reservation.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data.get("checkin_token"))

    def test_checkin_by_token_malformed_token_returns_400(self):
        """
        UUID形式でないtoken(QRスキャナーの誤読等を想定)は
        500ではなく400になる
        """
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            "/api/cinema/staff/checkin-by-token/",
            {"token": "not-a-valid-uuid"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)