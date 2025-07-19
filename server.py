from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)
RECIPIENT_FILE = 'recipients.json'

@app.route('/add-email', methods=['POST'])
def add_email():
    email = request.json.get('email')
    if not email:
        return jsonify({'message': '⚠️ 이메일이 유효하지 않습니다.'}), 400

    recipients = []
    if os.path.exists(RECIPIENT_FILE):
        with open(RECIPIENT_FILE, 'r') as f:
            recipients = json.load(f)

    if email in recipients:
        return jsonify({'message': '⚠️ 이미 등록된 이메일입니다.'}), 400

    recipients.append(email)
    with open(RECIPIENT_FILE, 'w') as f:
        json.dump(recipients, f, indent=2)

    return jsonify({'message': f'✅ 이메일이 로컬에 저장되었습니다: {email}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
