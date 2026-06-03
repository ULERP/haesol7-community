"""
PythonAnywhere 무료 계정 월 자동 갱신 스크립트
매월 1일 실행 권장 — PA Scheduled Tasks에 등록
"""
import urllib.request
import urllib.parse
import os

PA_USER  = os.environ.get('PA_USERNAME', 'ULERP')
PA_TOKEN = os.environ.get('PA_API_TOKEN', '')  # PA 대시보드 → Account → API Token

def renew_webapp():
    url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{PA_USER}.pythonanywhere.com/reload/'
    req = urllib.request.Request(
        url,
        method='POST',
        headers={'Authorization': f'Token {PA_TOKEN}'}
    )
    try:
        with urllib.request.urlopen(req) as res:
            print(f"✅ 웹앱 리로드 성공: {res.status}")
    except Exception as e:
        print(f"❌ 실패: {e}")

def extend_free_account():
    """무료 계정 3개월 연장 — PA 웹 콘솔에서 수동 클릭 필요"""
    print("⚠️  무료 계정 연장은 https://www.pythonanywhere.com/account/ 에서 수동으로 진행하세요.")
    print("    매월 말일 전에 'Extend expiry date' 버튼 클릭 필요")

if __name__ == '__main__':
    if not PA_TOKEN:
        print("❌ PA_API_TOKEN 환경변수를 설정하세요")
        print("   PA 대시보드 → Account → API Token 에서 발급")
    else:
        renew_webapp()
    extend_free_account()
