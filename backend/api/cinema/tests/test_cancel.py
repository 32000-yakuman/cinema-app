from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from api.cinema.models import (
    Theater, Screen, Movie, Showtime,
    Reservation, Payment,
    cancel_reservation, PaymentAlreadyConfirmed,
)

User = get_user_model()


class CancelReservationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            username="admin-user", password="test-password", is_staff=True
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

    def _create_reservation(self, payment_method=None, payment_status=None):
        reservation = Reservation.objects.create(
            user=self.customer,
            showtime=self.showtime,
            total_price=1500,
            status=Reservation.Status.CONFIRMED,
        )
        if payment_method is not None:
            Payment.objects.create(
                reservation=reservation,
                amount=1500,
                method=payment_method,
                status=payment_status,
            )
        return reservation

    def test_customer_cannot_cancel_after_point_payment_confirmed(self):
        """
        ポイント決済確定済みの予約は、引き続き顧客自身ではキャンセルできない
        """
        reservation = self._create_reservation(
            payment_method=Payment.Method.POINT, payment_status=Payment.Status.CONFIRMED,
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(f"/api/cinema/reservations/{reservation.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CONFIRMED)

    def test_admin_can_force_cancel_after_cash_payment_confirmed(self):
        """
        管理者は現金決済確定済みの予約でも強制キャンセルできる(窓口で返金対応する想定)
        """
        reservation = self._create_reservation(
            payment_method=Payment.Method.CASH, payment_status=Payment.Status.CONFIRMED,
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(f"/api/cinema/admin/reservations/{reservation.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CANCELLED)
        reservation.payment.refresh_from_db()
        self.assertEqual(reservation.payment.status, Payment.Status.CANCELLED)

    def test_cancel_reservation_raises_for_confirmed_payment_by_default(self):
        """
        cancel_reservation()を直接呼んだ場合も、
        allow_after_payment_confirmed=Falseなら決済確定済みの予約は例外になる
        """
        reservation = self._create_reservation(
            payment_method=Payment.Method.CASH, payment_status=Payment.Status.CONFIRMED,
        )

        with self.assertRaises(PaymentAlreadyConfirmed):
            cancel_reservation(reservation)
