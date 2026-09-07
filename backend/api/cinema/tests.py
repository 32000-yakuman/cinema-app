import threading
import uuid
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from api.cinema.models import (
    Theater, Screen, Seat, Movie, Showtime,
    Reservation, ReservationSeat, Payment, UserPoint,
    cancel_reservation, PaymentAlreadyConfirmed,
    create_reservation, POINT_EARN_PER_VIEW,
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
            start_time=timezone.now(),
            end_time=timezone.now(),
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


class AdminUserTogglePartialUpdateTests(TestCase):
    """
    AdminUserDetailView.patch()の回帰テスト。

    以前はpartial=Trueが指定されておらず、フロントが1フィールドだけ
    送るPATCHリクエスト(例: {"is_staff": true})を送ると、リクエストに
    含まれていない他のフラグ(is_active, is_staff_member)がモデルの
    デフォルト値で意図せず上書きされてしまうバグがあった。
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="admin-user", password="test-password", is_staff=True
        )

    def test_patching_one_flag_does_not_reset_other_flags(self):
        """
        is_staffだけを更新しても、is_staff_memberとis_activeの
        現在の値が保たれること
        """
        target_user = User.objects.create_user(
            username="target-user",
            password="test-password",
            is_staff_member=True,
            is_active=False,
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            f"/api/cinema/admin/users/{target_user.id}/",
            {"is_staff": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target_user.refresh_from_db()

        # 更新対象のフラグは反映されていること
        self.assertTrue(target_user.is_staff)
        # 更新対象外のフラグは維持されていること
        # (以前のバグではis_staff_memberがFalse、is_activeがTrueに
        #  リセットされていた)
        self.assertTrue(target_user.is_staff_member)
        self.assertFalse(target_user.is_active)


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