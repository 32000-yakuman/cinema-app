#!/bin/bash
# 初回のLet's Encrypt証明書発行スクリプト
# EC2上でこのリポジトリのルート(docker-compose.ymlがある場所)で1回だけ実行する。
#
# 手順:
#  1. certbotがまだ本物の証明書を持っていないので、nginxが参照できる
#     「ダミー証明書」を一時的に作成する(nginxを先に起動するため)。
#  2. nginxを起動する(この時点ではダミー証明書でhttps応答)。
#  3. ダミー証明書を消し、certbotに本物の証明書をHTTP-01チャレンジで発行させる。
#  4. nginxをreloadして本物の証明書に切り替える。

set -e

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

domain="ghostly-field-theater.com"
email=${MY_EMAIL_ADDRESS}   # 有効期限切れ通知が届くメールアドレスに変更してください
data_path="./certbot"
rsa_key_size=4096

if [ -d "$data_path" ]; then
  read -p "既存の $data_path が見つかりました。削除して続行しますか？ (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

echo "### ダミー証明書を作成しています ..."
mkdir -p "$data_path/conf/live/$domain"
docker compose -f docker-compose.prod.yml run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '/etc/letsencrypt/live/$domain/privkey.pem' \
    -out '/etc/letsencrypt/live/$domain/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

echo "### nginxを起動しています ..."
docker compose -f docker-compose.prod.yml up --force-recreate -d nginx
echo

echo "### ダミー証明書を削除しています ..."
docker compose -f docker-compose.prod.yml run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$domain && \
  rm -Rf /etc/letsencrypt/archive/$domain && \
  rm -Rf /etc/letsencrypt/renewal/$domain.conf" certbot
echo

echo "### Let's Encryptに本物の証明書を要求しています ..."
docker compose -f docker-compose.prod.yml run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $email \
    -d $domain \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --no-eff-email \
    --force-renewal" certbot
echo

echo "### nginxを再読み込みしています ..."
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload