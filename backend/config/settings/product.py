from .base import *

DEBUG = False

# 本番環境のドメインを入力
ALLOWED_HOSTS = ["ghostly-field-theater.com"]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "https://ghostly-field-theater.com",
]

#本番環境はHTTPS
CSRF_TRUSTED_ORIGINS = [ 
    "https://ghostly-field-theater.com", 
]

CSRF_COOKIE_SECURE = True 
SESSION_COOKIE_SECURE = True 

# JWT Cookie 
JWT_COOKIE_SECURE = True
JWT_COOKIE_SAMESITE = "Lax"

# HSTS: 本番はhttpsのみで運用するためブラウザに常時https強制を指示する
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30日。安定稼働を確認後、1年(31536000)まで伸ばす想定
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False # 安定運用できたらTrueに
 
# 本番ではDEBUGレベルのアプリログを出さない(リクエスト内容等の漏えい防止)
LOGGING["loggers"]["api.cinema"]["level"] = "INFO"