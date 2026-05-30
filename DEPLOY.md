# PythonAnywhere 배포 가이드

## 1. PythonAnywhere 계정 준비
- https://www.pythonanywhere.com 에서 무료 계정 생성
- username.pythonanywhere.com 도메인 자동 제공

## 2. Bash 콘솔에서 실행

```bash
# DEPLOY.md 생성
cat > /workspaces/haesol7-community/DEPLOY.md << 'EOF'
# PythonAnywhere 배포 가이드

## 1. PythonAnywhere 계정 준비
- https://www.pythonanywhere.com 에서 무료 계정 생성
- username.pythonanywhere.com 도메인 자동 제공

## 2. Bash 콘솔에서 실행

```bash
# Git clone
git clone https://github.com/ULERP/haesol7-community.git
cd haesol7-community

# 가상환경 생성
python3.12 -m venv .venv
source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성
cat > .env << 'ENVEOF'
SECRET_KEY=여기에-50자-이상-랜덤-문자열-입력
DEBUG=False
ALLOWED_HOSTS=your-username.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://your-username.pythonanywhere.com
ANTHROPIC_API_KEY=
ENVEOF

# DB 마이그레이션
python manage.py migrate

# 관리자 계정 생성
python manage.py createsuperuser

# Static 파일 수집
python manage.py collectstatic --noinput
```

## 3. Web 탭 설정
- Source code: /home/your-username/haesol7-community
- Working directory: /home/your-username/haesol7-community
- Virtualenv: /home/your-username/haesol7-community/.venv
- WSGI file: 아래 내용으로 수정

## 4. WSGI 설정 (PythonAnywhere Web탭 > WSGI file 클릭)

```python
import os
import sys

path = '/home/your-username/haesol7-community'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'hello_world.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## 5. Static Files 설정 (Web탭 > Static files)
- URL: /static/
- Directory: /home/your-username/haesol7-community/staticfiles
- URL: /media/
- Directory: /home/your-username/haesol7-community/hello_world/media

## 6. Reload 버튼 클릭 → 완료!
