from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import (
    Theater, Screen, Seat, Movie, Showtime,
    Reservation, ReservationSeat, Payment,
    UserPoint, PointTransaction,
    POINT_EARN_PER_VIEW, POINT_REDEEM_COST
)


class TheaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theater
        fields = ['id', 'name', 'address']


class ScreenSerializer(serializers.ModelSerializer):
    theater_name = serializers.CharField(source='theater.name', read_only=True)

    class Meta:
        model = Screen
        fields = ['id', 'theater', 'theater_name', 'name', 'row_count', 'col_count']


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ['id', 'screen', 'row_label', 'seat_number', 'seat_type']


class MovieSerializer(serializers.ModelSerializer):
    rating_display = serializers.CharField(source='get_rating_display', read_only=True)

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'description', 'duration_minutes',
            'release_date', 'rating', 'rating_display',
        ]


class ShowtimeSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    screen_name = serializers.CharField(source='screen.name', read_only=True)
    theater_name = serializers.CharField(source='screen.theater.name', read_only=True)

    class Meta:
        model = Showtime
        fields = [
            'id', 'movie', 'movie_title', 'screen', 'screen_name', 'theater_name',
            'start_time', 'end_time', 'base_price',
        ]


class ReservationSeatSerializer(serializers.ModelSerializer):
    seat_label = serializers.SerializerMethodField()

    class Meta:
        model = ReservationSeat
        fields = ['id', 'seat', 'seat_label', 'showtime', 'price']
        read_only_fields = ['showtime']

    def get_seat_label(self, obj):
        return f"{obj.seat.row_label}{obj.seat.seat_number}"


class ReservationSerializer(serializers.ModelSerializer):
    seats = ReservationSeatSerializer(source='reservationseat_set', many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'user', 'showtime', 'status', 'status_display',
            'reserved_at', 'total_price', 'seats',
        ]
        read_only_fields = ['user', 'status', 'reserved_at', 'total_price']


class ReservationCreateSerializer(serializers.Serializer):
    """
    予約作成専用の入力バリデーション用シリアライザ
    実際の作成処理はmodels.pyのcreate_reservation()を呼び出す
    """
    showtime_id = serializers.IntegerField()
    seat_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )


class PaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'reservation', 'amount', 'method',
            'status', 'status_display', 'paid_at'
        ]

class PaymentCreateSerializer(serializers.Serializer):
    """
    決済方法を選択して支払いを作成する専用シリアライザ
    """
    method = serializers.ChoiceField(choices=Payment.Method)

    def create(self, validated_data):
        reservation = self.context["reservation"]
        user = self.context["request"].user
        method = validated_data["method"]

        with transaction.atomic():
            if method == Payment.Method.POINT:
                user_point, _ = UserPoint.objects.select_for_update().get_or_create(user=user)
                if user_point.balance < POINT_REDEEM_COST:
                    raise serializers.ValidationError("ポイント残高が不足しています")

                user_point.balance -= POINT_REDEEM_COST
                user_point.save()

                PointTransaction.objects.create(
                    user=user, reservation=reservation,
                    type=PointTransaction.Type.REDEEM, amount=-POINT_REDEEM_COST,
                )
                payment = Payment.objects.create(
                    reservation=reservation, method=Payment.Method.POINT,
                    status=Payment.Status.CONFIRMED, points_used=POINT_REDEEM_COST,
                    amount=0, confirmed_at=timezone.now(),
                )
                reservation.status = Reservation.Status.CONFIRMED
                reservation.save()
            else:
                payment = Payment.objects.create(
                    reservation=reservation, method=Payment.Method.CASH,
                    status=Payment.Status.PENDING, amount=reservation.total_price,
                )
        return payment


class PaymentConfirmSerializer(serializers.Serializer):
    """
    窓口職員が現金決済を最終確定する
    """
    def save(self, **kwargs):
        payment = self.context["payment"]
        staff_user = self.context["request"].user

        if payment.status != Payment.Status.PENDING:
            raise serializers.ValidationError("この決済はすでに確定済み、またはキャンセル済みです")

        payment.status = Payment.Status.CONFIRMED
        payment.confirmed_by = staff_user
        payment.confirmed_at = timezone.now()
        payment.save()

        payment.reservation.status = Reservation.Status.CONFIRMED
        payment.reservation.save()
        return payment

        
class CheckInSerializer(serializers.Serializer):
    """
    窓口職員が来場確認を行う。同時にポイント付与も実行
    """
    def save(self, **kwargs):
        reservation = self.context["reservation"]

        if reservation.checked_in_at:
            raise serializers.ValidationError("すでにチェックイン済みです")
        if not hasattr(reservation, "payment") or reservation.payment.status != Payment.Status.CONFIRMED:
            raise serializers.ValidationError("`決済が確定していないため、チェックインできません")

        with transaction.atomic():
            reservation.checked_in_at = timezone.now()
            reservation.save()

            user_point, _ = UserPoint.objects.select_for_update().get_or_create(user=reservation.user)
            user_point.balance += POINT_EARN_PER_VIEW
            user_point.save()

            PointTransaction.objects.create(
                user=reservation.user, reservation=reservation,
                type=PointTransaction.Type.EARN, amount=POINT_EARN_PER_VIEW,
            )
        return reservation


class UserPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPoint
        fields = ["balance"]