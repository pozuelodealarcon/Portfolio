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

    # 기본 초기값
    path = RECIPIENT_FILE
    data = []

    try:
        contents = repo.get_contents(path)
        data = json.loads(contents.decoded_content.decode())

        if new_email not in data:
            data.append(new_email)
            updated_content = json.dumps(data, indent=2)
            repo.update_file(
                path=path,
                message=f"Add email {new_email}",
                content=updated_content,
                sha=contents.sha
            )
            return True
        else:
            return False

    except Exception as e:
        # 파일이 없는 경우 (404), 새로 생성
        if hasattr(e, 'status') and e.status == 404:
            print(f"File not found on GitHub, creating new: {path}")
            data = [new_email]
            updated_content = json.dumps(data, indent=2)
            repo.create_file(
                path=path,
                message=f"Create recipients file and add {new_email}",
                content=updated_content
            )
            return True
        else:
            print(f"GitHub API error: {e}")
            raise


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
