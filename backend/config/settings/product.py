from .base import *

DEBUG = False

# 本番環境のドメインを入力
ALLOWED_HOSTS = ["*"]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

#本番環境はHTTPS
#CSRF_TRUSTED_ORIGINS = [ "https://example.com", ]

CSRF_COOKIE_SECURE = True 
SESSION_COOKIE_SECURE = True 

# JWT Cookie 
JWT_COOKIE_SECURE = True
JWT_COOKIE_SAMESITE = "None"