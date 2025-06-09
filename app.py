from flask import Flask, request, render_template, redirect
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
DATA_FILE = 'posts.txt'

# メール設定：環境変数から取得
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASS = os.environ.get('SMTP_PASS')
TO_EMAIL   = os.environ.get('TO_EMAIL', SMTP_USER)  # 指定なければ自分に送信

# 投稿をファイルに保存
def save_post(content):
    with open(DATA_FILE, 'a', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

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
def index():
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            save_post(content)
            send_email(content)
        return redirect('/')
    posts = load_posts()
    return render_template('index.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True)
