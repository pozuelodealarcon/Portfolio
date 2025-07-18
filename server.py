from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

RECIPIENT_FILE = 'recipients.json'

# 이메일 리스트 로드
def load_recipients():
    if os.path.exists(RECIPIENT_FILE):
        with open(RECIPIENT_FILE, 'r') as f:
            return json.load(f)
    return []

# 이메일 저장
def save_recipients(recipients):
    with open(RECIPIENT_FILE, 'w') as f:
        json.dump(recipients, f, indent=2)

@app.route('/add-email', methods=['POST'])
def add_email():
    email = request.json.get('email')
    if not email:
        return jsonify({'message': '⚠️ 이메일이 유효하지 않습니다.'}), 400

    recipients = load_recipients()
    if email in recipients:
        return jsonify({'message': '⚠️ 이미 등록된 이메일입니다.'}), 400

    recipients.append(email)
    save_recipients(recipients)
    return jsonify({'message': f'✅ Email added: {email}'})

# ✅ Railway-compatible entrypoint
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

