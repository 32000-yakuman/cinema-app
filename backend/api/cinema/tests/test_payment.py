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


class PaymentConfirmViewTests(TestCase):
    """
    ReservationPaymentConfirmView(窓口の現金決済確定処理)の回帰テスト。

    PaymentConfirmSerializer.save()は以前、Payment.pkを誤って
    Reservationのpkとして扱っており、Payment.pkとReservation.pkが
    たまたま一致しない場合に「無関係な別の予約」を確定させてしまう
    バグがあった。このテストはそれを再現・検知する。
    """

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

    def _create_reservation(self):
        return Reservation.objects.create(
            user=self.customer,
            showtime=self.showtime,
            total_price=1500,
            status=Reservation.Status.PENDING,
        )

    def test_confirm_targets_correct_reservation_when_ids_diverge(self):
        """
        Payment.pkとReservation.pkがずれていても、
        窓口確定操作は正しい予約だけを確定させること
        """
        # ① 決済を作らない「おとり」の予約を先に1件作る。
        #    これでReservationのpkだけが1つ進み、Paymentのpkとは
        #    ずれた状態を意図的に作り出す(この時点でdecoy.pk=1)。
        decoy_reservation = self._create_reservation()

        # ② 本命の予約(pk=2)を作り、その決済(pk=1)を作成する。
        #    → payment.pk(1) != target_reservation.pk(2) となり、
        #      修正前のコードなら別の予約(decoy)を確定させてしまう状況を再現できる。
        target_reservation = self._create_reservation()
        payment = Payment.objects.create(
            reservation=target_reservation,
            amount=1500,
            method=Payment.Method.CASH,
            status=Payment.Status.PENDING,
        )

        # 前提条件（IDが実際にずれていること）を明示的に確認しておく。
        # ここが等しくなってしまうとテストの意味がなくなるため念のため検証する。
        self.assertNotEqual(payment.pk, target_reservation.pk)

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.patch(
            f"/api/cinema/reservations/{target_reservation.pk}/payment/confirm/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        target_reservation.refresh_from_db()
        decoy_reservation.refresh_from_db()
        payment.refresh_from_db()

        # ③ 正しい予約(target_reservation)側が確定していること
        self.assertEqual(target_reservation.status, Reservation.Status.CONFIRMED)
        self.assertEqual(payment.status, Payment.Status.CONFIRMED)
        self.assertEqual(payment.confirmed_by_id, self.staff_user.id)

        # ④ 無関係な予約(decoy_reservation)は一切変化していないこと。
        #    修正前のバグではここが誤ってCONFIRMEDになっていた。
        self.assertEqual(decoy_reservation.status, Reservation.Status.PENDING)

class ReservationPaymentViewTests(TestCase):
    """
    ReservationPaymentView(決済方法の選択)の回帰テスト。

    現金決済を選んだ時点で、上映開始まで座席を確保できるよう
    Reservation.expires_atがNoneにクリアされることを確認する。
    """

    def setUp(self):
        self.client = APIClient()

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

        self.reservation = Reservation.objects.create(
            user=self.customer,
            showtime=self.showtime,
            total_price=1500,
            status=Reservation.Status.PENDING,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        self.client.force_authenticate(user=self.customer)

    def test_cash_payment_clears_expires_at(self):
        """現金決済を選択すると、expires_atがNoneにクリアされ
        座席が上映開始まで確保され続けること"""
        response = self.client.post(
            f"/api/cinema/reservations/{self.reservation.pk}/payment/",
            {"method": "cash"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.reservation.refresh_from_db()
        self.assertIsNone(self.reservation.expires_at)
        self.assertEqual(self.reservation.status, Reservation.Status.PENDING)

    def test_point_payment_does_not_touch_expires_at_handling(self):
        """ポイント決済はstatusがCONFIRMEDになるため、
        expires_atの値にかかわらずexpire_pending_reservationsの対象外になること"""
        UserPoint.objects.create(user=self.customer, balance=10)

        response = self.client.post(
            f"/api/cinema/reservations/{self.reservation.pk}/payment/",
            {"method": "point"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.Status.CONFIRMED)