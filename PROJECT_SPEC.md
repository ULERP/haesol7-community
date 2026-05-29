# 해솔마을7단지 지킴이 커뮤니티 앱 — PROJECT SPEC

## 기본 정보
- GitHub: https://github.com/ULERP/haesol7-community
- 환경: GitHub Codespaces
- 서버: python manage.py runserver 0.0.0.0:8000
- venv: source /workspaces/haesol7-community/.venv/bin/activate
- 관리자: admin / haesol7777
- URL: https://redesigned-space-tribble-vpv47p4v496wcwrvj-8000.app.github.dev

## 기술 스택
- Django 5.2 + SQLite + Bootstrap 5
- 메인앱: hello_world/core/
- 커뮤니티앱: community/
- 템플릿: hello_world/templates/
- 공통레이아웃: base.html, base_3panel.html, chat_base.html

## 완성된 기능
- 회원가입/로그인/마이페이지/프로필수정 (닉네임, 동/호 분리)
- 6단계 회원 등급 시스템
- 게시판 CRUD/말머리/이미지첨부/페이지네이션/등급별 권한
- 봉사활동 달력 + 참가신청 (FullCalendar.js)
- 활동 인증 제출/목록/관리자 승인 → 마일리지/배지 자동 발급
- 이웃 온기 점수 (Rating 모델 + 프로필 별점 평가)
- 알림 시스템
- 관리문서 게시판 (/community/docs/)
- 채팅 3패널 메인 (홈화면)
- 전체채팅 (PublicChat)
- 1:1 쪽지/채팅 (DirectMessage)
- 소모임 CRUD + 채팅 연동 + 게시판
- 채팅 미니 투표 (ChatPoll)
- 게시글 ↔ 채팅 연동 (토론하기 모달)
- 게시글 ↔ 설문 연동 (삽입 + 자동 댓글)
- 관련 게시글 연결 (ManyToMany)
- 설문조사 시스템 (10가지 유형 + 통계 대시보드)
- 마이페이지 통합 대시보드
- 3패널 레이아웃 전체 통일 (base_3panel.html)
- RAG 챗봇 UI (API키 미설정)

## 모델 목록
CustomUser(닉네임/동/호), Badge, Activity, ActivityProof,
ActivityVerification, UserBadge, Rating, Board, Category,
Post(related_posts/linked_survey), PostImage, Comment, PostLike,
Trade, Poll, Choice, Event, Notification, ChatHistory,
ManagementDocument, Group, GroupMember, Meetup, GroupPost,
GroupComment, GroupChat, MemberGrade, BoardGradePermission,
DirectMessage, PublicChat, Survey, SurveyQuestion, SurveyResponse,
ChatPoll

## URL 구조
/ → 홈 (3패널 채팅 메인)
/chat/dm/list/ → 1:1 채팅 목록
/chat/dm/<id>/ → 1:1 채팅방
/chat/group/<id>/ → 소모임 채팅방
/groups/ → 소모임 목록
/groups/<pk>/posts/ → 소모임 게시판
/community/docs/ → 관리문서
/surveys/ → 설문조사
/volunteer/ → 봉사달력
/boards/ → 게시판
/chatbot/ → AI 챗봇
/users/<id>/ → 입주민 프로필

## 내일 최우선 작업
1. 로그아웃 버튼 동작 확인
2. 네비게이션 정렬 최종 확인
3. Git 커밋 & 코드 정리

## 다음 작업 목록 (우선순위)

### 긴급
- [ ] 로그아웃 동작 수정
- [ ] 네비게이션 한 줄 정렬
- [ ] Git 커밋 & requirements.txt 정리

### 쪽지/채팅 이원화
- [ ] 쪽지함 (받은/보낸/답장) — 마이페이지 통합
- [ ] 1:1 실시간 채팅 (로그인 상태 전용)
- [ ] 친구/이웃 목록 관리

### 소모임 개선
- [ ] 소모임 검색/필터/카테고리
- [ ] 페이지네이션
- [ ] 외부 홍보 (공개 페이지/SNS 공유/QR코드)

### 단지 통계 대시보드
- [ ] 인구 구성/시설 이용 통계 수집
- [ ] 차트 시각화 대시보드
- [ ] 설문 → 통계 자동 연계

### 관리문서 개선
- [ ] 게시판 카테고리 통합 + 전문 검색
- [ ] PDF 업로드/미리보기
- [ ] RAG 챗봇 연동 (ANTHROPIC_API_KEY 필요)

### 봉사달력 → 일정 통합
- [ ] 봉사 + 소모임 + 단지행사 통합 캘린더
- [ ] 일정 알림/구독/자동 등록

### 배포
- [ ] PythonAnywhere 배포
- [ ] 모바일 UI 최적화 (PWA)

## 주의사항
- hello_world/urls.py: include('hello_world.core.urls') + include('community.urls') 유지
- chat_base.html: 채팅 전용 3패널 레이아웃
- base_3panel.html: 일반 페이지 3패널 레이아웃
- signals.py: apps.py ready()에서 자동 등록
- context_processors.py: 공통 우측 패널 데이터 (공지/설문/봉사)
- .env: ANTHROPIC_API_KEY 설정 시 챗봇 활성화
