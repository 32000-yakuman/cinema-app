# 在庫管理システム

## 概要
Django + Next.js + MySQL による在庫管理アプリケーション

## 構成
- backend: Django REST Framework
- frontend: Next.js (App Router)
- nginx: リバースプロキシ（TLS終端）
- MySQL 8.0

## セットアップ手順（開発環境）
1. .env を作成し、必要な環境変数を設定
2. `docker-compose.override.yml` を作成（ローカル用ポート公開）
   ​```yaml
   services:
     app-db:
       ports:
         - "3307:3306"
     backend:
       ports:
         - "8000:8000"
     frontend:
       ports:
         - "3001:3000"
   ​```
3. docker compose up -d --build
4. 初回のみ: python manage.py createsuperuser

## 環境変数

`.env` ファイルをプロジェクトルートに作成し、以下の変数を設定してください。

| 変数名 | 説明 | 例 |
|---|---|---|
| `MYSQL_ROOT_PASSWORD` | MySQLのrootパスワード | （任意の文字列） |
| `MYSQL_APP_PASSWORD` | アプリ専用ユーザーのパスワード | （任意の文字列） |
| `MYSQL_DATABASE` | 使用するデータベース名 | `app_db` |
| `DJANGO_SECRET_KEY` | Djangoの署名用シークレットキー | `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` で生成 |
| `DJANGO_SETTINGS_MODULE` | 使用する設定ファイル | `config.settings.development` |
| `NODE_ENV` | Next.jsの実行モード | `development` または `production` |

## テスト実行
```bash
docker compose exec backend python manage.py test
```
## URL
- ローカル開発: https://localhost/
- 本番: （ドメイン取得後に追記）

## 前提条件
- Docker / Docker Compose
- Git

## 注意点
・djangoのルーティング規約に合わせてパスの末尾に/をつけること（フロント側も）
ex.) path("admin/", admin.site.urls)
　　  axios.get("/api/inventory/me/")
・models.pyにかかわる変更をしたらマイグレーションでDBに変更を伝えること