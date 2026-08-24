from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('theaters/', views.TheaterView.as_view()),
    path('theaters/<int:id>/', views.TheaterView.as_view()),
    path('screens/', views.ScreenView.as_view()),
    path('screens/<int:id>/', views.ScreenView.as_view()),
    path('seats/', views.SeatView.as_view()),
    path('movies/', views.MovieView.as_view()),
    path('movies/<int:id>/', views.MovieView.as_view()),
    path('showtimes/', views.ShowtimeView.as_view()),
    path('showtimes/<int:id>/', views.ShowtimeView.as_view()),
    path('reservations/', views.ReservationView.as_view()),
    path('reservations/<int:id>/', views.ReservationView.as_view()),
    path('reservations/<int:id>/cancel/', views.ReservationCancelView.as_view()),
    path('payments/', views.PaymentView.as_view()),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', views.LoginView.as_view()),
    path('retry/', views.RetryView.as_view()),
    path('logout/', views.LogoutView.as_view()),
    path('me/', views.MeView.as_view()),
]