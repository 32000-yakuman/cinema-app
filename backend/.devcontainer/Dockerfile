# ベースイメージ（Python 3.11）
FROM python:3.11-slim

# 必要な Linux パッケージ（MySQLclient に必須）
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    default-mysql-client \
    && apt-get clean \
    && pip install mysqlclient \ 
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# Python の依存関係を先にコピーしてインストール
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# アプリケーションコードをコピー
COPY . /app/

# entrypoint.sh をコピー
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Django のポート
EXPOSE 8000

# 起動コマンド（entrypoint に任せる）
ENTRYPOINT ["/entrypoint.sh"]
