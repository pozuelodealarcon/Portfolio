from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from github import Github  # PyGithub

app = Flask(__name__, static_folder="cool-vue-app/dist", static_url_path="")

CORS(app, resources={r"/*": {"origins": "*"}})

RECIPIENT_FILE = 'recipients.json'

# GitHub 설정
GITHUB_TOKEN = os.environ.get('GITHUB_PAT')  # Railway 환경변수에 저장 필요
GITHUB_REPO = 'pozuelodealarcon/Portfolio'

def update_recipients_on_github(new_email):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    try:
        contents = repo.get_contents(RECIPIENT_FILE)
        data = json.loads(contents.decoded_content.decode())
        sha = contents.sha  # 필수
    except Exception as e:
        print(f"[WARN] get_contents 실패: {e}")
        return False  # 실제로는 파일이 있으므로 create_file() 시도하면 안 됨

    if new_email not in data:
        data.append(new_email)
        updated_content = json.dumps(data, indent=2)
        try:
            repo.update_file(
                path=RECIPIENT_FILE,
                message=f"Add email {new_email}",
                content=updated_content,
                sha=sha  # 여기 반드시 있어야 함
            )
            return True
        except Exception as e:
            print(f"[ERROR] update_file 실패: {e}")
            return False
    else:
        print(f"[INFO] 이미 존재하는 이메일: {new_email}")
        return False


@app.route('/add-email', methods=['POST'])

def add_email():
    email = request.json.get('email')
    if not email:
        return jsonify({'message': '⚠️ 이메일이 유효하지 않습니다.'}), 400

    # 로컬 파일도 업데이트 (필요 시)
    recipients = []
    if os.path.exists(RECIPIENT_FILE):
        with open(RECIPIENT_FILE, 'r') as f:
            recipients = json.load(f)
    if email in recipients:
        return jsonify({'message': '⚠️ 이미 등록된 이메일입니다.'}), 400
    recipients.append(email)
    with open(RECIPIENT_FILE, 'w') as f:
        json.dump(recipients, f, indent=2)

    # GitHub 저장소 업데이트 시도
    if update_recipients_on_github(email):
        return jsonify({'message': f'✅ Email added and pushed to GitHub: {email}'})
    else:
        return jsonify({'message': f'✅ Email added locally (already in GitHub): {email}'})


@app.route('/')
def serve_vue():
    return app.send_static_file('index.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
