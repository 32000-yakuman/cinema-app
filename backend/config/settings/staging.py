from .base import *

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# staging環境のドメインが決まっていれば設定（未定なら保留）
# CSRF_TRUSTED_ORIGINS = [ "https://staging.example.com", ]