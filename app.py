import os
import time
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
TOKENS_FILE  = 'kakao_tokens.json'
CLIENT_ID    = 'cffae5a613ce4e125271ca9aa9289f06'
REDIRECT_URI = 'https://kakao-oauth-server.onrender.com/oauth/kakao/callback'

@app.route('/oauth/kakao/callback')
def kakao_callback():
    code = request.args.get('code')
    if not code:
        return 'code 파라미터가 없습니다.', 400

    tokens = requests.post(
        'https://kauth.kakao.com/oauth/token',
        data={
            'grant_type':    'authorization_code',
            'client_id':     CLIENT_ID,
            'redirect_uri':  REDIRECT_URI,
            'code':          code
        }
    ).json()
    tokens['issued_at'] = time.time()
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)

    return '''
    <!DOCTYPE html>
    <html lang="ko"><head><meta charset="UTF-8"><title>서비스 이용 안내</title></head>
    <body>
      <h1>서비스를 정상 이용 하실 수 있습니다.</h1>
      <p>메시지 발송까지 최대 10분 소요될 수 있습니다.</p>
    </body>
    </html>
    '''

@app.route('/oauth/kakao/token')
def get_kakao_token():
    if not os.path.exists(TOKENS_FILE):
        return jsonify({'error': '토큰이 존재하지 않습니다.'}), 404

    with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
        tokens = json.load(f)

    now = time.time()
    expires_at = tokens['issued_at'] + tokens['expires_in']
    # 만료 시 refresh
    if now > expires_at:
        resp = requests.post(
            'https://kauth.kakao.com/oauth/token',
            data={
                'grant_type':    'refresh_token',
                'client_id':     CLIENT_ID,
                'refresh_token': tokens['refresh_token']
            }
        )
        if resp.status_code != 200:
            return jsonify({'error': '토큰 갱신 실패'}), 401
        new = resp.json()
        tokens.update({
            'access_token':  new.get('access_token', tokens['access_token']),
            'expires_in':    new.get('expires_in', tokens['expires_in']),
            'refresh_token': new.get('refresh_token', tokens['refresh_token'])
        })
        tokens['issued_at'] = now
        with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, ensure_ascii=False, indent=2)

    return jsonify(tokens)

if __name__ == '__main__':
    # Render (or Heroku 등) 배포 환경에서 제공하는 PORT 환경변수
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
