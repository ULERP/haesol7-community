# 해솔마을7단지 지킴이 커뮤니티 앱 — PROJECT SPEC
> 최종 업데이트: 2026-06-03

## 기본 정보
- GitHub: https://github.com/ULERP/haesol7-community
- 서비스: https://ulerp.pythonanywhere.com
- PythonAnywhere: ULERP 계정
- 관리자: admin / haesol7777

## 시작 명령어
cd /workspaces/haesol7-community
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000

## PA 배포
cd ~/haesol7-community && git pull origin main && python manage.py migrate --noinput && python manage.py collectstatic --noinput && touch /var/www/ulerp_pythonanywhere_com_wsgi.py && echo "완료"

## 기술 스택
- Django 5.2 + SQLite + Bootstrap 5
- 메인앱: hello_world/core/
- 커뮤니티앱: community/
- 이메일: Gmail SMTP (hs7guardian@gmail.com / yenoqzlochowpzpd)
- R2: 준비됨, PA SSL 이슈로 보류

## 레이아웃
- base_2panel.html: 모든 내부 페이지 (사이드바+메인+우측패널)
- index.html: 홈 전용 3패널 토글
- chat_base.html: 채팅 전용
- context processor: sidebar_chats, sidebar_hot_posts, sidebar_online_users 자동주입

## 완성된 기능
- 회원가입/로그인/비밀번호찾기(보안질문+이메일)/임시비밀번호발급
- 게시판 CRUD + 등급별 권한
- 공지/민원/관리문서 게시판
- 전체채팅/1:1채팅/쪽지
- 소모임 CRUD + 게시판
- 봉사활동 달력 + 참가신청
- 활동인증 + 마일리지 + 배지 자동발급
- 이웃 온기 점수 (별점)
- 설문조사 시스템
- 티저 전략 (비로그인/미승인 블러+가입유도)
- 모바일 히어로+퀵메뉴+하단탭바+더보기패널
- 데스크탑 2패널 레이아웃 + 우측 라이브패널
- 홈 3패널 토글 대시보드
- 관리자 한글화 + AdminActionLog
- Gmail SMTP 이메일 발송

## 마이그레이션
- 0025: security_question/answer
- 0026: AdminActionLog
- 0027: verbose_name 한글화
- 0028: PublicChat.message TextField

## .env 키값
- EMAIL_HOST_USER=hs7guardian@gmail.com
- EMAIL_HOST_PASSWORD=yenoqzlochowpzpd
- R2_ACCOUNT_ID=c0d5773e71b9367dba67d84a5149e54
- R2_ACCESS_KEY_ID=f639fca04fb6c29f299e2f447bebc3a2
- R2_SECRET_ACCESS_KEY=0fa9097a004dee3af7ab8c696cea3b26fb7a8b8b8add7209999ec5a664323b
- R2_BUCKET_NAME=haesol7-media

## 다음 작업 우선순위
1. 사이드바 토글 고급화 (아이콘만 남기기, 버튼 개선)
2. 히어로 배경 이미지 관리자 업로드
3. 캘린더 강화 (공지/봉사/소모임 통합)
4. 메뉴 정리 (중복 제거)
5. R2 이미지 분리 (PA SSL 해결)
6. PA 월 자동 갱신 스크립트

## 주의사항
- PA 경로: /home/ULERP/haesol7-community/ (대문자!)
- .env는 git 제외, PA에 별도 설정 필요
- base_3panel.html은 레거시 (base_2panel로 전환 완료)

## 세션 2 완료 (2026-06-04)
- fix: chat_base.html regex/중복 버그 3건
- fix: 이미지 메시지 serialize 오류 (m.image.name)
- feat: 채팅 폴링 2초 + 낙관적 업데이트
- feat: cancelled 봉사활동 숨김
- feat: 404/500 에러 페이지 (이전페이지/홈 버튼)
## 디자인 가이드
### 현재 색상 (녹색 테마)
- 메인: `#1a7a4a` (녹색)
- 밝은 녹색: `#1e9158`
- 연녹색 배경: `#e8f5ee`
- CSS 변수: `--g: #1a7a4a`, `--gl: #e8f5ee`
### 목표 색상 테마 (롯데캐슬 스타일 — 추후 작업)
- 메인 다크 네이비: `#1F2937`
- 서브 와인 버건디: `#6E2332`
- 포인트 골드: `#C8A86B`
- 배경 아이보리: `#F8F7F3`
- 텍스트 다크 그레이: `#333333`
- 참고 이미지: 롯데캐슬 앱 UI (다크 네이비 사이드바 + 와인 버건디 강조 + 골드 버튼)
### 색상 테마 교체 작업 계획 (7~8시간 예상)
1. CSS 변수 시스템 구축 (`--primary`, `--secondary`, `--accent`, `--bg`, `--text`)
2. `base.html`, `base_2panel.html`, `chat_base.html` CSS 변수 전환
3. 각 템플릿 인라인 색상 → CSS 변수 전환
4. 관리자 페이지에서 테마 선택 UI (SiteConfig 활용)
5. Jazzmin 테마도 연동
### 현재 하드코딩된 주요 색상 위치
- `base.html` — navbar 배경
- `base_2panel.html` — 사이드바
- `chat_base.html` — 채팅 UI
- `mypage.html` — 프로필 헤더 그라디언트
- `volunteer_detail.html` — 봉사활동 헤더
- 각 템플릿 인라인 style 속성 수백 곳
### 관리자 색상 피커 (추후)
- `SiteConfig` 모델에 `hero_color` 필드 이미 존재
- 색상 피커 위젯 → 전체 CSS 변수 동적 업데이트 방식으로 구현 예정
### 모바일 UI
- 하단 탭바: 대화하기/기록하기/함께하기/단지소식 4개
- 퀵 액션 바: 동일 4개 카테고리
- 관리자 메시지 말풍선: 골드색 (모바일 디자인 추후 정리 필요)
### 폰트/아이콘
- Bootstrap 5 기본 폰트
- Font Awesome 6 (아이콘)
- Bootstrap Icons (bi-*) 일부 사용

## 세션 3 추가 작업 (2026-06-04 오후)
- feat: 게시판 목록 카드 UI (최근글 미리보기, 게시글수 강조, NEW 배지)
- feat: 게시판 2열 + 지킴이 아카이브 하단 가로형 전체폭
- feat: 기록하기 게시판 목록 5개로 정리 (나눔/장터, 건의FAQ 제외)
- feat: 네비바 기록하기 드롭다운 5개 게시판으로 정리
- feat: 함께하기/단지소식 허브 페이지 오류 수정
- 다음: 함께하기 허브에 나눔/장터 추가, 단지소식 허브에 FAQ/건의 추가


## 6. 업데이트 이력 (2026.06.06)

### 완료된 작업
- views.py 262번 줄 문법 오류 수정 (쉼표 두 개)
- 관리 문서 게시판  (management_docs 뷰, ManagementDocument 모델 활용)
- 이웃 온기 점수  (rating_list, rating_give 뷰 추가)
- 배지 자동 발급 헬퍼 (_auto_award_badge 함수 추가)
- 소모임 일정 추가 버튼 오류 수정 (GET→모달 POST 방식)
- Poll 모델 group FK 추가 (related_name='group_polls') + 마이그레이션 0037
- poll_create / poll_vote / poll_results 뷰 추가
- /polls/create/, /polls/<id>/vote/, /polls/<id>/results/ URL 등록
- PythonAnywhere 배포 및 동기화 완료

### 진행 중
- 소모임 상세 페이지: 설문조사 탭 UI + FullCalendar 달력 뷰
- 전체 공유 캘린더 (봉사활동 달력과 통합)

### 주의사항
- Poll.group related_name = 'group_polls' (ChatPoll.group과 충돌 방지)
- calendar_event_create 함수 views.py에 2개 존재 (2606, 2695번) → 2695번이 유효
- PA venv: /home/ULERP/haesol7-community/.venv (python3.12)
- PA reload: touch /var/www/ulerp_pythonanywhere_com_wsgi.py


## 7. 업데이트 이력 (2026.06.06 - 2차)

### 완료된 작업
- 소모임 일정 추가 모달 방식으로 수정 (GET→POST)
- FullCalendar 6.1.11 소모임 달력 탭 추가
- Poll 모델 group FK 추가 (related_name='group_polls') + migration 0037
- 소모임 설문조사 탭 추가 (만들기/투표/결과 실시간)
- poll_create / poll_vote / poll_results API 뷰 추가
- admin ActivityProof 승인 시 포인트 자동 적립 + 배지 자동 발급 연동
- calendar_event_create 중복 함수 존재 (2610, 2699번) → 추후 정리 필요

### 현재 URL 구조 (신규 추가분)
- /docs/ → 관리 문서 게시판
- /ratings/ → 이웃 온기 점수
- /ratings/give/<user_pk>/ → 평가하기
- /polls/create/ → 설문 생성 (POST JSON)
- /polls/<id>/vote/ → 투표 (POST JSON)
- /polls/<id>/results/ → 결과 조회 (GET JSON)
- /calendar/create/ → 일정 생성 (POST JSON)

### 배포 정보
- VS: GitHub Codespaces
- FA: https://ulerp.pythonanywhere.com
- PA venv: /home/ULERP/haesol7-community/.venv (python3.12)
- PA reload: touch /var/www/ulerp_pythonanywhere_com_wsgi.py
- 관리자: admin / haesol7777
