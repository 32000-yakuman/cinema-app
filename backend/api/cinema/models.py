from django.db import models, transaction
from django.conf import settings
import uuid


class Theater(models.Model):
    """
    劇場
    """
    name = models.CharField(max_length=100, verbose_name='劇場名')
    address = models.CharField(max_length=200, verbose_name='住所')

    class Meta:
        db_table = 'theater'
        verbose_name = '劇場'

class Screen(models.Model):
    """
    スクリーン
    """
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name='スクリーン名')
    row_count = models.PositiveIntegerField(verbose_name='座席の行数')
    col_count = models.PositiveIntegerField(verbose_name='座席の列数')
    

    class Meta:
        db_table = 'screen'
        verbose_name = 'スクリーン'
        verbose_name_plural = 'スクリーン一覧'

class Seat(models.Model):
    """
    座席
    """
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE)
    row_label = models.CharField(max_length=10, verbose_name='行ラベル')
    seat_number = models.PositiveIntegerField(verbose_name="席番号")
    seat_type = models.CharField(max_length=100, verbose_name="席タイプ")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["screen", "row_label", "seat_number"],
                name="unique_seat_per_screen"
            )
        ]
        db_table = 'seat'
        verbose_name = '座席'

class Movie(models.Model):
    """
    映画
    """
    title = models.CharField(max_length=100, verbose_name='タイトル')
    # 長文のためmax_lemgth不要
    description = models.TextField(blank=True, verbose_name='あらすじ') 
    duration_minutes = models.PositiveIntegerField(verbose_name='上映時間')
    release_date = models.DateField(verbose_name='公開日')

    class Rating(models.TextChoices):
        G = "G", "全年齢"
        PG12 = "PG12", "PG12"
        R15 = "R15", "R15"
        R18 = "R18", "R18"
        
    rating = models.CharField(
        max_length=10,
        choices=Rating.choices,
        default='G',
        verbose_name='レーティング'
    )
    

    class Meta:
        db_table = 'movie'
        verbose_name = '映画'

class Showtime(models.Model):
    """
    上映回
    """
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE)
    start_time = models.DateTimeField(verbose_name="上映開始時間")
    end_time = models.DateTimeField(verbose_name="上映終了時間")
    base_price = models.PositiveIntegerField(verbose_name="基本料金")

    class Meta:
        db_table = 'showtime'
        verbose_name = '上映回'

class Reservation(models.Model):
    """
    予約
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    #予約の入った上映回を消さないためにProtect
    showtime = models.ForeignKey(Showtime, on_delete=models.PROTECT)
    reserved_at = models.DateTimeField(auto_now_add=True, verbose_name="予約日時")
    total_price = models.PositiveIntegerField(verbose_name="合計金額")
    checked_in_at = models.DateTimeField(null=True, blank=True, verbose_name="来場確認日時")

    # チェックインQRコード用トークン
    checkin_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="チェックイン用トークン"
    )

    class Status(models.TextChoices):
        PENDING = "pending", "仮押さえ"  
        CONFIRMED ="confirmed", "確定"
        CANCELLED = "cancelled",  "キャンセル"

    status = models.CharField(max_length=20,
                                choices=Status.choices,
                                default=Status.PENDING,
                                verbose_name='予約状態')

    class Meta:
        db_table = 'reservation'
        verbose_name = '予約'

class ReservationSeat(models.Model):
    """
    予約座席
    """
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.PROTECT)
    showtime = models.ForeignKey(Showtime, on_delete=models.PROTECT)
    price = models.PositiveIntegerField(verbose_name="座席価格")

    '''
    ここから二重予約を防ぐための処理
    '''
    # 予約座席を記憶するモジュール
    def save(self, *args, **kwargs):
        self.showtime = self.reservation.showtime
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'reservation_seat'
        verbose_name = '予約座席'
        constraints = [
            models.UniqueConstraint(
                fields=["seat", "showtime"],
                name="unique_seat_per_showtime"
            )
        ]

class SeatLimitExceeded(Exception):
    """
    1アカウントにつき座席数上限（5席）を超えた場合
    """
    pass

class InvalidSeatSelection(Exception):
    """
    指定された座席IDが存在しない、または上映回のスクリーンに属さない場合
    """
    pass

# 予約座席を確保
@transaction.atomic
def create_reservation(user, showtime, seat_ids):
    seat_ids = list(seat_ids)
    seats = list(Seat.objects.select_for_update().filter(id__in=seat_ids))

    # ⓵ 存在しないseat_idが混ざっていないのか
    founds_ids = {s.id for s in seats}
    if founds_ids != set(seat_ids):
        raise InvalidSeatSelection("指定された座席が見つかりません")

    # ⓶ この上映会のスクリーンに属する座席か
    if any(s.screen_id != showtime.screen_id for s in seats):
        raise InvalidSeatSelection("選択した座席はこの上映回のスクリーンに対応していません")


    existing_count = ReservationSeat.objects.filter(
        reservation__user=user,
        reservation__showtime=showtime,
        reservation__status__in=[Reservation.Status.PENDING, Reservation.Status.CONFIRMED],
    ).count()
    if existing_count + len(seat_ids) > 5:
        raise SeatLimitExceeded(
            f"同じ上映回では1アカウントにつき5座席までです(現在{existing_count}席予約済み)"
        )

    reservation = Reservation.objects.create(
        user=user, showtime=showtime, status=Reservation.Status.PENDING, total_price=0
    )
    # 金額の初期化
    total = 0
    for seat in seats:
        rs = ReservationSeat.objects.create(
        reservation=reservation, seat=seat, price=showtime.base_price
    )
        total += rs.price
    reservation.total_price = total
    reservation.save()
    return reservation

class AlreadyCheckedIn(Exception):
    """
    チェックイン済みの予約はキャンセル不可
    """
    pass

# キャンセル時に予約座席を消去
@transaction.atomic
def cancel_reservation(reservation):
    if reservation.checked_in_at:
        raise AlreadyCheckedIn("チェックイン済みの予約はキャンセルできません")
    reservation.status = Reservation.Status.CANCELLED
    reservation.save()
    ReservationSeat.objects.filter(reservation=reservation).delete()

    # ポイント決済だったら、ポイントを返還
    if hasattr(reservation, "payment") and reservation.payment.method == Payment.Method.POINT:
        payment = reservation.payment
        if payment.status == Payment.Status.CONFIRMED:
            user_point, _ = UserPoint.objects.select_for_update().get_or_create(user=reservation.user)
            user_point.balance += payment.points_used
            user_point.save()
            PointTransaction.objects.create(
                user=reservation.user, reservation=reservation,
                type=PointTransaction.Type.REFUND, amount=payment.points_used,
            )
            payment.status = Payment.Status.CANCELLED
            payment.save()



class Payment(models.Model):
    """
    決済
    """
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name="決済金額", default=0)

    class Method(models.TextChoices):
        CASH = "cash", "現金"
        POINT = "point", "ポイント交換"

    method = models.CharField(max_length=20, choices=Method.choices)

    class Status(models.TextChoices):
        PENDING = "pending", "仮確定(未払い)"
        CONFIRMED = "confirmed", "確定済み"
        CANCELLED = "cancelled",  "キャンセル"
    
    status = models.CharField(max_length=20, choices=Status.choices,
                              default=Status.PENDING, verbose_name="決済状態")
    
    points_used = models.PositiveIntegerField(default=0, verbose_name="使用ポイント数")
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="confirmed_payments",
        verbose_name="会計確定した職員"
    )
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="決済確定日時")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="決済完了日時")

    class Meta:
        db_table = 'payment'
        verbose_name = '決済'
        constraints = [
            models.CheckConstraint(
                check=~(models.Q(method="point") & models.Q(status="pending")),
                name="point_payment_cannot_be_pending",
            ),
        ]

POINT_EARN_PER_VIEW = 1
POINT_REDEEM_COST = 5

class UserPoint(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.PositiveIntegerField(default=0, verbose_name="保有ポイント")

    class Meta:
        db_table = 'user_point'
        verbose_name = 'ユーザーポイント'

class PointTransaction(models.Model):

    class Type(models.TextChoices):
        EARN = "earn", "付与"
        REDEEM = "redeem", "交換使用"
        REFUND = "refund", "返還"
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, null=True, blank=True, on_delete=models.SET_NULL)
    type = models.CharField(max_length=10, choices=Type.choices)
    amount = models.IntegerField(verbose_name="増減量(付与・返還は正、交換は負)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'point_transaction'
        verbose_name = 'ポイント履歴'