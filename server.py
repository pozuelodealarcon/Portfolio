import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder="cool-vue-app/dist", static_url_path="")
CORS(app, resources={r"/*": {"origins": "*"}})

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

    return jsonify({'message': f'✅ 구독이 정상 처리되었습니다: {email}'})

@app.route('/')
def serve_vue():
    return app.send_static_file('index.html')

@app.route('/')
def hourly_job():
    print("⏰ Hourly job ran - nothing to do here")
    return "Hourly job ran", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
