from django.core.files.storage import default_storage
from django.conf import settings
from django.db import IntegrityError
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework.permissions import IsAuthenticated

from .models import (
    Theater, Screen, Seat, Movie, Showtime,
    Reservation, ReservationSeat, Payment,
    create_reservation, cancel_reservation
)
from .serializers import (
    TheaterSerializer, ScreenSerializer, SeatSerializer,
    MovieSerializer, ShowtimeSerializer,
    ReservationSerializer, ReservationCreateSerializer, 
    PaymentSerializer,
)


class TheaterView(APIView):
    """
    劇場操作に関する関数
    """
    def get_object(self, pk):
        try:
            return Theater.objects.get(pk=pk)
        except Theater.DoesNotExist:
            raise NotFound

    
    def get(self, request, id=None, format=None):
        if id is None :
            queryset = Theater.objects.all()
            serializer = TheaterSerializer(queryset, many=True)
        else: 
            theater = self.get_object(id)
            serializer = TheaterSerializer(theater)
        return Response(serializer.data, status.HTTP_200_OK)


    def post(self, request, format=None):
        serializer = TheaterSerializer(data=request.data)
        # validationを通らなかった場合、例外を投げる
        serializer.is_valid(raise_exception=True)
        # 検証したデータを永続化する
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)


    def put(self, request, id, format=None):
        theater = self.get_object(id)
        serializer = TheaterSerializer(instance=theater, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_200_OK)


    def delete(self, request, id, format=None):
        theater = self.get_object(id)
        theater.delete()
        return Response(status = status.HTTP_200_OK)

class ScreenView(APIView):
    """
    スクリーン操作に関する関数
    """
    def get_object(self, pk):
        try:
            return Screen.objects.get(pk=pk)
        except Screen.DoesNotExist:
            raise NotFound

    
    def get(self, request, id=None, format=None):
        if id is None :
            queryset = Screen.objects.all()
            serializer = ScreenSerializer(queryset, many=True)
        else: 
            screen = self.get_object(id)
            serializer = ScreenSerializer(screen)
        return Response(serializer.data, status.HTTP_200_OK)


    def post(self, request, format=None):
        serializer = ScreenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)


    def put(self, request, id, format=None):
        screen = self.get_object(id)
        serializer = ScreenSerializer(instance=screen, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_200_OK)


    def delete(self, request, id, format=None):
        screen = self.get_object(id)
        screen.delete()
        return Response(status = status.HTTP_200_OK)
    
class SeatView(APIView):
    """
    座席操作に関する関数
    """    
    def get(self, request, format=None):
        screen_id = request.query_params.get('screen')
        if screen_id is None :
            return Response({"errMsg": "screenを指定してください"}, status.HTTP_400_BAD_REQUEST)
        queryset = Seat.objects.filter(screen_id=screen_id)
        serializer = SeatSerializer(queryset, many=True)
        return Response(serializer.data, status.HTTP_200_OK)


    def post(self, request, format=None):
        serializer = SeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)


class MovieView(APIView):
    """
    映画操作に関する関数
    """
    def get_object(self, pk):
        try:
            return Movie.objects.get(pk=pk)
        except Movie.DoesNotExist:
            raise NotFound

    
    def get(self, request, id=None, format=None):
        if id is None :
            queryset = Movie.objects.all()
            serializer = MovieSerializer(queryset, many=True)
        else: 
            movie = self.get_object(id)
            serializer = MovieSerializer(movie)
        return Response(serializer.data, status.HTTP_200_OK)


    def post(self, request, format=None):
        serializer = MovieSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)


    def put(self, request, id, format=None):
        movie = self.get_object(id)
        serializer = MovieSerializer(instance=movie, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_200_OK)


    def delete(self, request, id, format=None):
        movie = self.get_object(id)
        movie.delete()
        return Response(status = status.HTTP_200_OK)
    
class ShowtimeView(APIView):
    """
    上映回操作に関する関数
    """
    def get_object(self, pk):
        try:
            return Showtime.objects.get(pk=pk)
        except Showtime.DoesNotExist:
            raise NotFound

    
    def get(self, request, id=None, format=None):
        if id is None :
            queryset = Showtime.objects.all()
            movie_id = request.query_params.get('movie')
            if movie_id:
                queryset = queryset.filter(movie_id=movie_id)
            serializer = ShowtimeSerializer(queryset, many=True)
        else: 
            showtime = self.get_object(id)
            serializer = ShowtimeSerializer(showtime)
        return Response(serializer.data, status.HTTP_200_OK)


    def post(self, request, format=None):
        serializer = ShowtimeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)

class ReservationView(APIView):
    """
    予約操作に関する関数
    """
    def get(self, request, format=None):        
        # ログイン中のユーザー自身の予約のみ返す
        queryset = Reservation.objects.filter(user=request.user).order_by('-reserved_at')
        serializer = ReservationSerializer(queryset, many=True)
        return Response(serializer.data, status.HTTP_200_OK)


    def post(self, request, format=None):
        """
        座席を指定して予約を作成する
        """
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        showtime_id = serializer.validated_data['showtime_id']
        seat_ids = serializer.validated_data['seat_ids']

        try:
            showtime = Showtime.objects.get(pk=showtime_id)
        except Showtime.DoesNotExist:
            raise NotFound('指定された上映館が見当たりません')

        try:
            reservation = create_reservation(
                user=request.user, showtime=showtime, seat_ids=seat_ids
            )
        except IntegrityError:
            return Response(
                {"errMsg": "選択された座席はすでに予約されています"},
                status.HTTP_409_CONFLICT
            )
        
        result = ReservationSerializer(reservation)
        return Response(result.data, status.HTTP_201_CREATED)


class ReservationCancelView(APIView):
    """
    予約キャンセルに関する関数
    """
    def get_object(self, pk, user):
        try:
            return Reservation.objects.get(pk=pk, user=user)
        except Reservation.DoesNotExist:
            raise NotFound


    def post(self, request, id, format=None):
        reservation = self.get_object(id, request.user)
        cancel_reservation(reservation)
        serializer = ReservationSerializer(reservation)
        return Response(serializer.data, status.HTTP_200_OK)


class PaymentView(APIView):
    """
    決済操作に関する関数
    """
    def post(self, request, format=None):
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)

class LoginView(APIView):
    """ユーザーのログイン処理
    Args:
    APIView (class): rest_framework.viewsのAPIViewを受け取る
    """
    # 認証クラスの指定
    # リクエストヘッダーにtokenを差し込むといったカスタム動作をしないので素の認証クラスを使用する
    authentication_classes = []
    # アクセス許可の指定
    permission_classes = []

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"errMsg": "ユーザ名またはパスワードが正しくありません"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        access = serializer.validated_data.get("access", None)
        refresh = serializer.validated_data.get("refresh", None)
        if access:
            response = Response(status=status.HTTP_200_OK)
            max_age = settings.COOKIE_TIME
            response.set_cookie(
                'access',
                access,
                httponly=True,
                max_age=max_age,
                secure=settings.JWT_COOKIE_SECURE,
                samesite=settings.JWT_COOKIE_SAMESITE
            )

            response.set_cookie(
                'refresh',
                refresh,
                httponly=True,
                max_age=max_age,
                secure=settings.JWT_COOKIE_SECURE,
                samesite=settings.JWT_COOKIE_SAMESITE
            )
            return response
        return Response(
            {'errMsg': 'ユーザーの認証に失敗しました'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

class RetryView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # refresh を Cookie から読む（これが絶対必要）
        refresh_token = request.COOKIES.get('refresh')

        if not refresh_token:
            return Response({'errMsg': 'refresh token がありません'}, status=status.HTTP_401_UNAUTHORIZED)

        # TokenRefreshSerializer に渡す
        serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
        serializer.is_valid(raise_exception=True)

        access = serializer.validated_data.get("access")
        refresh = serializer.validated_data.get("refresh")

        if access:
            response = Response(status=status.HTTP_200_OK)
            max_age = settings.COOKIE_TIME
            response.set_cookie(
                'access',
                access,
                httponly=True,
                max_age=max_age,
                secure=settings.JWT_COOKIE_SECURE,
                samesite=settings.JWT_COOKIE_SAMESITE
            )

            response.set_cookie(
                'refresh',
                refresh,
                httponly=True,
                max_age=max_age,
                secure=settings.JWT_COOKIE_SECURE,
                samesite=settings.JWT_COOKIE_SAMESITE
            )
            return response

        return Response({'errMsg': 'ユーザーの認証に失敗しました'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args):
        response = Response(status=status.HTTP_200_OK)
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response
    
# ログイン認証用API
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user_id": request.user.id}, status=200)