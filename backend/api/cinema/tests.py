import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from api.cinema.models import (
    Theater, Screen, Seat, Movie, Showtime,
    Reservation, ReservationSeat, Payment, UserPoint,
    cancel_reservation, PaymentAlreadyConfirmed,
)

User = get_user_model()

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
            start_time=timezone.now(),
            end_time=timezone.now(),
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
            start_time=timezone.now(),
            end_time=timezone.now(),
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