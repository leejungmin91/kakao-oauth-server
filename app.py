from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "카카오 OAuth 콜백 서버 작동 중입니다."

@app.route('/oauth/kakao/callback')
def kakao_callback():
    code = request.args.get('code')
    if not code:
        return "code 파라미터가 없습니다.", 400

    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": "cffae5a613ce4e125271ca9aa9289f06",
        "redirect_uri": "https://kakao-oauth-server.onrender.com/oauth/kakao/callback",
        "code": code
    }

    res = requests.post(token_url, data=data)
    return "이제 서비스를 정상 이용 하실 수 있습니다."
