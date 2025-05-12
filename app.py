from flask import Flask, request, jsonify, redirect
import requests
import json
import os
import time
from urllib.parse import urlencode

app = Flask(__name__)
TOKENS_FILE = 'kakao_tokens.json'
CLIENT_ID    = 'cffae5a613ce4e125271ca9aa9289f06'
REDIRECT_URI = 'https://kakao-oauth-server.onrender.com/oauth/kakao/callback'
SCOPE        = 'profile_nickname,friends,talk_message'

# 카카오 인증 URL 생성

def authorize_url():
    params = {
        'client_id':     CLIENT_ID,
        'redirect_uri':  REDIRECT_URI,
        'response_type': 'code',
        'scope':         SCOPE
    }
    return 'https://kauth.kakao.com/oauth/authorize?' + urlencode(params)

# 콜백 엔드포인트: code 받아 토큰 교환 및 저장

@app.route('/oauth/kakao/callback')
def kakao_callback():
    code = request.args.get('code')
    if not code:
        return 'code 파라미터가 없습니다.', 400

    # authorization_code → tokens 발급
    res = requests.post(
        'https://kauth.kakao.com/oauth/token',
        data={
            'grant_type':    'authorization_code',
            'client_id':     CLIENT_ID,
            'redirect_uri':  REDIRECT_URI,
            'code':          code
        }
    )
    if res.status_code != 200:
        return f'Token 교환 실패: {res.text}', res.status_code

    tokens = res.json()
    tokens['issued_at'] = time.time()
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)

    # 사용자 안내
    return '''
<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>서비스 이용 안내</title></head>
<body>
  <h1>서비스를 정상 이용 하실 수 있습니다.</h1>
  <p>메시지 발송까지 최대 10분 소요될 수 있습니다.</p>
</body>
</html>
    '''

# 토큰 조회/갱신 엔드포인트

@app.route('/oauth/kakao/token')
def get_kakao_token():
    # 토큰 파일 없으면 인증 유도
    if not os.path.exists(TOKENS_FILE):
        return redirect(authorize_url())

    with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
        tokens = json.load(f)

    now = time.time()
    expires_at = tokens.get('issued_at', 0) + tokens.get('expires_in', 0)
    if now > expires_at:
        # refresh_token으로 갱신
        resp = requests.post(
            'https://kauth.kakao.com/oauth/token',
            data={
                'grant_type':    'refresh_token',
                'client_id':     CLIENT_ID,
                'refresh_token': tokens.get('refresh_token')
            }
        )
        if resp.status_code != 200:
            return redirect(authorize_url())
        new = resp.json()
        tokens.update({
            'access_token':  new.get('access_token', tokens['access_token']),
            'expires_in':    new.get('expires_in', tokens.get('expires_in')),
            'refresh_token': new.get('refresh_token', tokens.get('refresh_token'))
        })
        tokens['issued_at'] = now
        with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, ensure_ascii=False, indent=2)

    return jsonify(tokens)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
