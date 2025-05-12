from flask import Flask, request
import requests, json, os, time

app = Flask(__name__)
TOKENS_FILE = 'kakao_tokens.json'
CLIENT_ID    = 'cffae5a613ce4e125271ca9aa9289f06'
REDIRECT_URI = 'https://kakao-oauth-server.onrender.com/oauth/kakao/callback'

@app.route('/oauth/kakao/callback')
def kakao_callback():
    code = request.args.get('code')
    if not code:
        return 'code 파라미터가 없습니다.', 400

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
        return f'Token exchange failed: {res.text}', res.status_code

    # 응답 토큰 저장
    tokens = res.json()
    tokens['issued_at'] = time.time()
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)

    # 사용자 안내 HTML
    return '''
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>서비스 이용 안내</title>
</head>
<body>
  <h1>서비스를 정상 이용 하실 수 있습니다.</h1>
  <p>메시지 발송까지 최대 10분 소요될 수 있습니다.</p>
</body>
</html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
