from django.db import models
from django.contrib.auth.models import User
from django.db import transaction

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #予約の入った上映回を消さないために
    showtime = models.ForeignKey(Showtime, on_delete=models.PROTECT)
    reserved_at = models.DateTimeField(auto_now_add=True, verbose_name="予約日時")
    total_price = models.PositiveIntegerField(verbose_name="合計金額")

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

# 予約座席を確保
@transaction.atomic
def create_reservation(user, showtime, seat_ids):
    seats = Seat.objects.select_for_update().filter(id__in=seat_ids)

    reservation = Reservation.objects.create(
        user=user, showtime=showtime, status=Reservation.Status.PENDING, total_price=0
    )
    # 金額の初期化
    total=0
    for seat in seats:
        rs = ReservationSeat.objects.create(
        reservation=reservation, seat=seat, price=showtime.base_price
    )
        total += rs.price
    reservation.total_price = total
    reservation.save()
    return reservation

# キャンセル時に予約座席を消去
@transaction.atomic
def cancel_reservation(reservation):
    reservation.status = Reservation.Status.CANCELLED
    reservation.save()
    ReservationSeat.objects.filter(reservation=reservation).delete()


class Payment(models.Model):
    """
    決済
    """
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name="決済金額")
    method = models.CharField(max_length=20, verbose_name="決済方法")
    # 現地払いもあるのでnullable
    paid_at = models.DateTimeField(null=True, verbose_name="決済完了日時") 

    class Status(models.TextChoices):
        PENDING = "pending", "仮押さえ"  
        PAID = "paid", "決済済"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='決済状態'
        )
        
    class Meta:
        db_table = 'payment'
        verbose_name = '決済'