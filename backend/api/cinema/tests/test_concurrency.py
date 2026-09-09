import threading
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from api.cinema.models import (
    Theater, Screen, Seat, Movie, Showtime,
    Reservation, ReservationSeat, Payment, UserPoint,
    create_reservation, POINT_EARN_PER_VIEW,
)

User = get_user_model()


class ConcurrentAccessTests(TransactionTestCase):
    """
    決済・キャンセル・チェックインまわりの負荷テスト(同時アクセス)。
 
    通常のTestCaseは1つのDBトランザクションで全体を包んでしまい、
    別スレッドからの同時アクセスを正しく再現できないため、
    ここではTransactionTestCaseを使う。各スレッドはDjangoの
    スレッドローカルなDB接続を使うため、スレッド終了時に
    connection.close()で明示的に閉じている。
    """
 
    def setUp(self):
        self.theater = Theater.objects.create(name="テスト劇場", address="テスト住所")
        self.screen = Screen.objects.create(
            theater=self.theater, name="スクリーン1", row_count=5, col_count=5
        )
        self.movie = Movie.objects.create(
            title="テスト映画", duration_minutes=120,
            release_date=timezone.now().date(),
        )
        self.showtime = Showtime.objects.create(
            movie=self.movie, screen=self.screen,
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=3),
            base_price=1500,
        )
        self.seat = Seat.objects.create(
            screen=self.screen, row_label="A", seat_number=1, seat_type="standard"
        )
        self.staff_user = User.objects.create_user(
            username="staff-user", password="test-password", is_staff_member=True
        )
 
    def _run_in_parallel(self, fn_a, fn_b):
        results = {}
 
        def wrap(fn, key):
            try:
                fn(results, key)
            finally:
                # スレッドごとのDB接続を明示的に閉じておく
                # (閉じないとテストDBの後片付け時にエラーになることがある)
                connection.close()
 
        t1 = threading.Thread(target=wrap, args=(fn_a, "a"))
        t2 = threading.Thread(target=wrap, args=(fn_b, "b"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        return results
 
    def test_concurrent_reservation_same_seat_only_one_succeeds(self):
        """
        同じ座席に対する同時予約リクエストは、
        どちらか一方だけが成功し、座席が二重予約されないこと
        """
        user_a = User.objects.create_user(username="user-a", password="test-password")
        user_b = User.objects.create_user(username="user-b", password="test-password")
 
        def attempt(user):
            def _fn(results, key):
                try:
                    reservation = create_reservation(
                        user=user, showtime=self.showtime, seat_ids=[self.seat.id]
                    )
                    results[key] = ("ok", reservation.id)
                except Exception as e:
                    results[key] = ("error", type(e).__name__)
            return _fn
 
        results = self._run_in_parallel(attempt(user_a), attempt(user_b))
 
        outcomes = [results["a"][0], results["b"][0]]
        self.assertEqual(outcomes.count("ok"), 1, f"成功が1件ではない: {results}")
        self.assertEqual(outcomes.count("error"), 1, f"失敗が1件ではない: {results}")
 
        # 座席が実際に二重予約されていないこと
        self.assertEqual(
            ReservationSeat.objects.filter(
                seat=self.seat, showtime=self.showtime
            ).count(),
            1,
        )
 
    def test_concurrent_payment_confirm_only_one_succeeds(self):
        """
        窓口職員が同じ決済を(ダブルクリック等で)同時に確定操作しても、
        確定されるのは1回だけであること
        """
        customer = User.objects.create_user(username="customer-user", password="test-password")
        reservation = Reservation.objects.create(
            user=customer, showtime=self.showtime, total_price=1500,
            status=Reservation.Status.PENDING,
        )
        payment = Payment.objects.create(
            reservation=reservation, amount=1500,
            method=Payment.Method.CASH, status=Payment.Status.PENDING,
        )
 
        client_a = APIClient()
        client_a.force_authenticate(user=self.staff_user)
        client_b = APIClient()
        client_b.force_authenticate(user=self.staff_user)
 
        def attempt(client):
            def _fn(results, key):
                response = client.patch(
                    f"/api/cinema/reservations/{reservation.pk}/payment/confirm/"
                )
                results[key] = response.status_code
            return _fn
 
        results = self._run_in_parallel(attempt(client_a), attempt(client_b))
 
        codes = [results["a"], results["b"]]
        self.assertEqual(
            codes.count(status.HTTP_200_OK), 1,
            f"確定成功(200)が1件ではない: {results}",
        )
 
        payment.refresh_from_db()
        reservation.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.CONFIRMED)
        self.assertEqual(reservation.status, Reservation.Status.CONFIRMED)
 
    def test_concurrent_checkin_only_grants_point_once(self):
        """
        同じ予約に対する同時チェックイン(QR二重読み取り等)でも、
        チェックインとポイント付与は1回だけ行われること
        """
        customer = User.objects.create_user(username="customer-user2", password="test-password")
        reservation = Reservation.objects.create(
            user=customer, showtime=self.showtime, total_price=1500,
            status=Reservation.Status.CONFIRMED,
        )
        Payment.objects.create(
            reservation=reservation, amount=1500,
            method=Payment.Method.CASH, status=Payment.Status.CONFIRMED,
        )
 
        client_a = APIClient()
        client_a.force_authenticate(user=self.staff_user)
        client_b = APIClient()
        client_b.force_authenticate(user=self.staff_user)
 
        def attempt(client):
            def _fn(results, key):
                response = client.post(
                    f"/api/cinema/reservations/{reservation.pk}/check-in/"
                )
                results[key] = response.status_code
            return _fn
 
        results = self._run_in_parallel(attempt(client_a), attempt(client_b))
 
        codes = [results["a"], results["b"]]
        self.assertEqual(
            codes.count(status.HTTP_200_OK), 1,
            f"チェックイン成功(200)が1件ではない: {results}",
        )
 
        reservation.refresh_from_db()
        self.assertIsNotNone(reservation.checked_in_at)
 
        # ポイントが1回分しか付与されていないこと
        # (以前バグがあった場合、ここが2倍になってしまう)
        user_point = UserPoint.objects.get(user=customer)
        self.assertEqual(user_point.balance, POINT_EARN_PER_VIEW)