from flask import Flask, request, render_template, redirect
from flask_httpauth import HTTPBasicAuth
import os
import smtplib
import requests
import json
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
auth = HTTPBasicAuth()

# Basic認証の設定
USERNAME = os.environ.get('BASIC_AUTH_USERNAME', 'admin')
PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD', 'password')

@auth.verify_password
def verify_password(username, password):
    return username == USERNAME and password == PASSWORD

DATA_FILE = 'posts.txt'

# メール設定：環境変数から取得
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASS = os.environ.get('SMTP_PASS')
TO_EMAIL   = os.environ.get('TO_EMAIL', SMTP_USER)  # 指定なければ自分に送信

def get_ip_info(ip_address):
    try:
        response = requests.get(f'https://ipinfo.io/{ip_address}/json')
        if response.status_code == 200:
            data = response.json()
            return {
                'city': data.get('city', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'org': data.get('org', 'Unknown'),
                'loc': data.get('loc', 'Unknown'),
                'timezone': data.get('timezone', 'Unknown')
            }
    except Exception as e:
        print(f"Error fetching IP info: {e}")
    return None

# 投稿をファイルに保存
def save_post(content):
    # 基本情報を取得
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 追加のヘッダー情報を取得
    referer = request.headers.get('Referer', 'Unknown')
    accept_language = request.headers.get('Accept-Language', 'Unknown')
    
    # IP情報を取得
    ip_info = get_ip_info(ip_address)
    
    # 画面表示用の情報（シンプル版）
    display_info = f"\n---\n{timestamp}"
    
    # メール送信用の詳細情報
    email_content = f"新しい投稿がありました\n\n"
    email_content += f"投稿内容:\n{content}\n\n"
    email_content += f"詳細情報:\n"
    email_content += f"投稿日時: {timestamp}\n"
    email_content += f"IP: {ip_address}\n"
    email_content += f"UA: {user_agent}\n"
    email_content += f"言語設定: {accept_language}\n"
    email_content += f"参照元: {referer}\n"
    
    if ip_info:
        email_content += f"\n位置情報:\n"
        email_content += f"国: {ip_info['country']}\n"
        email_content += f"地域: {ip_info['region']}\n"
        email_content += f"都市: {ip_info['city']}\n"
        email_content += f"プロバイダ: {ip_info['org']}\n"
        email_content += f"タイムゾーン: {ip_info['timezone']}\n"
        email_content += f"緯度経度: {ip_info['loc']}\n"
    
    # ファイルには画面表示用の情報のみ保存
    with open(DATA_FILE, 'a', encoding='utf-8') as f:
        f.write(content + display_info.strip() + '\n')
    
    # メール送信
    send_email(email_content)

# 投稿一覧を読み込み
def load_posts():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

# メール送信関数
def send_email(content):
    if not SMTP_USER or not SMTP_PASS:
        print("⚠️ SMTP_USER or SMTP_PASS is not set. Skipping email.")
        return

    msg = MIMEText(content)
    msg['Subject'] = '新しい投稿がありました'
    msg['From'] = SMTP_USER
    msg['To'] = TO_EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def index():
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            save_post(content)
        return redirect('/')
    posts = load_posts()
    return render_template('index.html', posts=posts)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
