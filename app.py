from flask import Flask, request, jsonify
import requests
import json
import os
import time

app = Flask(__name__)
TOKENS_FILE = 'kakao_tokens.json'
CLIENT_ID    = 'cffae5a613ce4e125271ca9aa9289f06'
REDIRECT_URI = 'https://kakao-oauth-server.onrender.com/oauth/kakao/callback'

# 전역 변수에 마지막으로 수신한 authorization code 저장
latest_code = None

@app.route('/oauth/kakao/callback')
def kakao_callback():
    global latest_code
    code = request.args.get('code')
    if not code:
        return 'code 파라미터가 없습니다.', 400

    # 받은 code를 가로채서 저장
    latest_code = code

    # 카카오 토큰 교환 요청
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

    # 응답 토큰 저장
    tokens = res.json()
    tokens['issued_at'] = time.time()
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)

    # 사용자 안내 페이지
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

@app.route('/oauth/kakao/code')
def get_code():
    """
    최근 callback에서 수신한 code를 반환하는 엔드포인트
    클라이언트 스크립트가 이 endpoint를 폴링하여 code를 가져올 수 있습니다.
    """
    if latest_code is None:
        # 아직 code가 수신되지 않았으면 204 No Content
        return '', 204
    return jsonify({'code': latest_code})

if __name__ == '__main__':
    # 외부 접근 허용
    app.run(host='0.0.0.0', port=8000)
