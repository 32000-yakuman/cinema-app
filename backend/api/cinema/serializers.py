from rest_framework import serializers
from .models import (
    Theater, Screen, Seat, Movie, Showtime,
    Reservation, ReservationSeat, Payment,
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