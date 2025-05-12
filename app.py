from flask import Flask, request, jsonify, redirect
import json
import os
import time
from urllib.parse import urlencode

app = Flask(__name__)
TOKENS_FILE = 'kakao_tokens.json'
CLIENT_ID    = 'cffae5a613ce4e125271ca9aa9289f06'
REDIRECT_URI = 'https://kakao-oauth-server.onrender.com/oauth/kakao/callback'
SCOPE        = 'profile_nickname,friends,talk_message'


def authorize_url():
    params = {
        'client_id':     CLIENT_ID,
        'redirect_uri':  REDIRECT_URI,
        'response_type': 'code',
        'scope':         SCOPE
    }
    return 'https://kauth.kakao.com/oauth/authorize?' + urlencode(params)

@app.route('/oauth/kakao/callback')
def kakao_callback():
    code = request.args.get('code')
    if not code:
        return 'code 파라미터가 없습니다.', 400

    # authorization code로 access/refresh token 발급
    token_url = 'https://kauth.kakao.com/oauth/token'
    data = {
        'grant_type':    'authorization_code',
        'client_id':     CLIENT_ID,
        'redirect_uri':  REDIRECT_URI,
        'code':          code
    }
    res = requests.post(token_url, data=data)
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

@app.route('/oauth/kakao/token')
def get_kakao_token():
    # 토큰 파일이 없으면 로그인 페이지로 리다이렉트
    if not os.path.exists(TOKENS_FILE):
        return redirect(authorize_url())

    with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
        tokens = json.load(f)

    # 토큰 만료 여부 확인 (만료 시 refresh)
    now = time.time()
    expires_at = tokens.get('issued_at', 0) + tokens.get('expires_in', 0)
    if now > expires_at:
        # refresh token으로 갱신
        refresh_url = 'https://kauth.kakao.com/oauth/token'
        refresh_data = {
            'grant_type':    'refresh_token',
            'client_id':     CLIENT_ID,
            'refresh_token': tokens.get('refresh_token')
        }
        resp = requests.post(refresh_url, data=refresh_data)
        if resp.status_code != 200:
            # 갱신 실패 시 재인가 필요
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

    # 유효한 토큰 반환
    return jsonify(tokens)

if __name__ == '__main__':
    # Render 환경의 PORT 환경변수 지원
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
