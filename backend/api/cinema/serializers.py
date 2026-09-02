from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers
from .models import (
    Theater, Screen, Seat, Movie, Showtime,
    Reservation, ReservationSeat, Payment,
    UserPoint, PointTransaction,
    POINT_EARN_PER_VIEW, POINT_REDEEM_COST
)
from accounts.models import CustomUser

User = get_user_model()

class TheaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theater
        fields = ['id', 'name', 'address']


class ScreenSerializer(serializers.ModelSerializer):
    theater_name = serializers.CharField(source='theater.name', read_only=True)

    class Meta:
        model = Screen
        fields = ['id', 'theater', 'theater_name', 'name', 'row_count', 'col_count']

    def create(self, validated_data):
        screen = Screen.objects.create(**validated_data)
        self._generate_seats(screen)
        return screen

    def _generate_seats(self, screen):
        import string
        seats = [
            Seat(
                screen=screen,
                row_label=string.ascii_uppercase[row],
                seat_number=col + 1,
                seat_type='standard'
            )
        for row in range(screen.row_count)
        for col in range(screen.col_count)
        ]
        Seat.objects.bulk_create(seats)


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

    def validate(self, data):
        start_time = data.get('start_time', getattr(self.instance, 'start_time', None))
        end_time = data.get('end_time', getattr(self.instance, 'end_time', None))
        screen = data.get('screen', getattr(self.instance, 'screen', None))

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                {"end_time":"終了時刻は開始時刻より後にしてください"}
            )

        if screen and start_time and end_time:
            overlapping = Showtime.objects.filter(
                screen=screen,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise serializers.ValidationError(
                    {"start_time":"同じスクリーンで時間帯が重複する上映回が既に存在します"}
                )
        return data


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
    payment_status = serializers.CharField(source="payment.status", read_only=True)
    payment_status_display = serializers.CharField(source="payment.get_status_display", read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'user', 'showtime', 'status', 'status_display',
            'reserved_at', 'total_price', 'seats',
            'payment_status', 'payment_status_display'
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

class StaffReservationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    customer_name = serializers.SerializerMethodField()
    movie_title = serializers.CharField(source="showtime.movie.title", read_only=True,)
    screen_name = serializers.CharField(source="showtime.screen.name", read_only=True,)
    payment_status = serializers.CharField(source="payment.status", read_only=True)
    payment_status_display = serializers.CharField(source="payment.get_status_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True,)
    seats = ReservationSeatSerializer(source='reservationseat_set',many=True,read_only=True,)

    def get_customer_name(self, obj):
        name = f"{obj.user.last_name} {obj.user.first_name}".strip()
        return name if name else obj.user.username

    class Meta:
        model = Reservation
        fields = [
            'id', 'user', 'username', 'screen_name', 'status', 'status_display',
            'checked_in_at', 'reserved_at', 'total_price', 'seats', 'showtime',
            'customer_name', 'movie_title', 'payment_status', 'payment_status_display'
        ]
        read_only_fields = ['user', 'status', 'reserved_at','total_price',]
    

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
            raise serializers.ValidationError("決済が確定していないため、チェックインできません")

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

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("このユーザー名は既に使われています")
        return value

    def validate_password(self, value):
        try:
            django_validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )

class AdminMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'duration_minutes', 'release_date', 'rating']

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'date_joined', 'is_staff_member', 'is_active', 'is_staff',
        ]
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'date_joined',]
