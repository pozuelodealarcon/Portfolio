import base64
import json
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder="cool-vue-app/dist", static_url_path="")
CORS(app, resources={r"/*": {"origins": "*"}})

RECIPIENT_FILE = 'recipients.json'
GITHUB_TOKEN = os.environ.get('GITHUB_PAT')
REPO = 'pozuelodealarcon/Portfolio'
BRANCH = 'main'  # 기본 브랜치명

def get_file_sha():
    url = f'https://api.github.com/repos/{REPO}/contents/{RECIPIENT_FILE}?ref={BRANCH}'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()['sha'], res.json()['content']
    return None, None

def update_or_create_file(new_email):
    sha, content_b64 = get_file_sha()
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}

    if content_b64:
        decoded = base64.b64decode(content_b64).decode()
        data = json.loads(decoded)
    else:
        data = []

    if new_email in data:
        return False, '이미 존재하는 이메일입니다.'

    data.append(new_email)
    new_content = json.dumps(data, indent=2)
    encoded_content = base64.b64encode(new_content.encode()).decode()

    payload = {
        "message": f"Add email {new_email}",
        "content": encoded_content,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha

    put_url = f'https://api.github.com/repos/{REPO}/contents/{RECIPIENT_FILE}'
    response = requests.put(put_url, headers=headers, data=json.dumps(payload))

    if response.status_code in [200, 201]:
        return True, 'GitHub에 이메일이 성공적으로 추가되었습니다.'
    else:
        return False, f'GitHub 업데이트 실패: {response.status_code} {response.text}'

@app.route('/add-email', methods=['POST'])
def add_email():
    email = request.json.get('email')
    if not email:
        return jsonify({'message': '⚠️ 이메일이 유효하지 않습니다.'}), 400

    # 로컬 파일 업데이트
    recipients = []
    if os.path.exists(RECIPIENT_FILE):
        with open(RECIPIENT_FILE, 'r') as f:
            recipients = json.load(f)
    if email in recipients:
        return jsonify({'message': '⚠️ 이미 등록된 이메일입니다.'}), 400
    recipients.append(email)
    with open(RECIPIENT_FILE, 'w') as f:
        json.dump(recipients, f, indent=2)

    # GitHub 업데이트 시도
    success, msg = update_or_create_file(email)
    if success:
        return jsonify({'message': f'✅ {msg}'})
    else:
        return jsonify({'message': f'⚠️ {msg}'}), 500

@app.route('/')
def serve_vue():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
