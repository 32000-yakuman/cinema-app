#!/bin/bash
# ローカルでnginxの起動・ルーティングだけを確認するためのダミー証明書を作る。
# 本物の証明書ではないため、ブラウザでは「保護されていない通信」の警告が出るが、
# nginxが起動してhttps応答することは確認できる。
#
# ドメイン取得・EC2デプロイ後は、この内容は使わず init-letsencrypt.sh で
# 本物のLet's Encrypt証明書に差し替えること。

set -e

domain="ghostly-field-theater.com"
cert_path="./certbot/conf/live/$domain"

mkdir -p "$cert_path"

openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
  -keyout "$cert_path/privkey.pem" \
  -out "$cert_path/fullchain.pem" \
  -subj "/CN=$domain"

echo "ダミー証明書を作成しました: $cert_path"
echo "docker compose up -d --build nginx で起動確認してください。"