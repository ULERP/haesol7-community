# 🏘️ 해솔7 커뮤니티 - 4가지 핵심 인터랙션 기능 구현 가이드

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [설치 및 실행](#설치-및-실행)
3. [4가지 핵심 기능](#4가지-핵심-기능)
4. [API 엔드포인트](#api-엔드포인트)
5. [데이터 모델](#데이터-모델)

---

## 🎯 프로젝트 개요

**해솔7 커뮤니티**는 주민 참여율과 공동체 활성화를 높이기 위해 AI & IT 기술을 접목한 4가지 핵심 기능을 제공합니다.

### 기술 스택
- **백엔드**: Django 5.2, Django REST Framework
- **데이터베이스**: SQLite (개발), PostgreSQL (프로덕션)
- **LLM**: OpenAI GPT-3.5, Anthropic Claude
- **인증**: Django Session, DRF TokenAuth

---

## 🚀 설치 및 실행

### 1. 환경 설정
```bash
# 패키지 설치
pip install -r requirements.txt

# 마이그레이션 적용
python manage.py migrate

# 초기 데이터 생성
python manage.py init_data
```

### 2. 개발 서버 시작
```bash
python manage.py runserver
```

### 3. 접속 정보
- **관리자 페이지**: http://localhost:8000/admin/
  - ID: `admin`
  - PW: `admin123!`
- **API 문서**: http://localhost:8000/api/
- **테스트 사용자**
  - user1 / test1234
  - user2 / test1234
  - user3 / test1234

---

## 💎 4가지 핵심 기능

### ① 마일리지 & 배지 시스템 (Gamification)

**주민의 봉사 참여를 시각화하여 성취감을 부여합니다.**

#### 활동 인증 및 크레딧
- 지킴이 활동(`야간 순찰`, `펫 매너 캠페인`, `환경 정비` 등)을 앱에서 인증
- 활동 시간과 포인트가 자동으로 적립됨
- 관리자가 증빙사진을 검토하여 승인/반려

#### 디지털 배지 & 감사장 발급
- 누적 활동에 따라 자동으로 배지 지급
  - `우리 동네 보안관` (500P, 20회 활동)
  - `그린 가디언` (400P, 15회 활동)
  - `펫 프렌드` (300P, 10회 활동)
  - `공동체의 별` (600P, 25회 활동)
- 연말에 모바일 감사장(PDF) 자동 발급

#### 데이터 흐름
```
지킴이 활동 인증 제출
    ↓
[관리자 검토/승인]
    ↓
포인트 적립 + 배지 자동 확인
    ↓
배지 획득 조건 충족 → 배지 지급 + 알림 발송
```

**주요 모델**:
- `Activity`: 활동 카테고리
- `ActivityProof`: 활동 인증 기록
- `Badge`: 배지 정의
- `UserBadge`: 사용자 배지 획득 기록

---

### ② AI 기반 '이웃 온기' 매너 평가 (Manners Score)

**당근마켓의 매너온도처럼, 아파트 내 소통의 질을 높입니다.**

#### 이웃 온기 점수 산출
- **받은 평가** (50%): 다른 주민들의 ⭐ 평가
- **활동 참여도** (30%): 승인된 활동 횟수
- **커뮤니티 활동** (20%): 그룹 댓글, 게시글 등

#### 효과
- 이웃 간 상호존중 문화 정착
- 악성 댓글 완화
- 층간소음, 주차 등 분쟁 완화의 완충재

#### 실시간 계산
```
새로운 평가 추가
    ↓
자동으로 이웃 온기 점수 재계산
    ↓
프로필에 실시간 반영 (0-100)
```

**주요 모델**:
- `Rating`: 주민 간 매너 평가
- `CustomUser.manners_score`: 이웃 온기 점수

---

### ③ LLM 기반 '동네 에이전트' 알림 및 가이드

**알림 메시지하나도 따뜻한 이웃의 목소리로 전달합니다.**

#### 페르소나 알림봇
- 공지사항/지킴이 모집을 AI가 친근한 말투로 자동 변환
  - "다정한 이웃": 따뜻함, 존댓
  - "자랑스러운 이웃": 축하, 응원
  - "따뜻한 동네": 포용, 공동체
  - "정보 도우미": 명확, 전문성

#### RAG 기반 관리 규약 챗봇
- 주민들이 주차, 펫, 소음 등에 대해 질문
- AI가 관리 규약 문서를 검색하여 쉬운 일상어로 답변
- 신뢰도 점수와 함께 답변 제공

#### 자동 감사장
- 연말에 활동 내역을 바탕으로 자동 생성
- PDF 형식으로 모바일 공유 가능

**주요 기능**:
- `NotificationGenerator`: 알림 메시지 자동 생성
- `RAGChatbot`: 규약 안내 챗봇
- `CertificateGenerator`: 감사장 자동 생성

---

### ④ 소그룹 기반 '동네 모임' 및 번개 (Hyper-Local Meetup)

**공동체 활성화의 꽃은 오프라인 만남입니다.**

#### 주민 주도 소그룹
- 주민들이 직접 소그룹 개설
  - `댕댕이 집사 모임`
  - `야간 가벼운 러닝`
  - `플로깅 (조깅하며 쓰레기 줍기)`

#### 번개(임시 모임) 기능
- 지킴이 단체의 정기 캠페인 외에도
- 주민들이 자발적으로 소소한 모임 개최
- 실시간 채팅 및 게시판

#### 소그룹 기능
- **그룹 생성/관리**: 리더가 그룹 운영
- **멤버 관리**: 역할(리더, 운영진, 일반) 구분
- **게시글 & 댓글**: 그룹 내 커뮤니티
- **실시간 채팅**: 그룹 채팅방
- **모임 일정**: 정기/임시 모임 관리

**주요 모델**:
- `Group`: 소그룹
- `GroupMember`: 그룹 멤버
- `Meetup`: 번개/임시 모임
- `GroupPost`: 그룹 게시글
- `GroupChat`: 그룹 채팅

---

## 📡 API 엔드포인트

### 인증 및 사용자

#### 사용자 프로필
```
GET    /api/users/me/                    # 현재 사용자 정보 (마일리지, 배지, 온기점수 포함)
PATCH  /api/users/me/                    # 프로필 수정
GET    /api/users/{id}/                  # 다른 사용자 프로필 조회
GET    /api/users/me/my-activities/      # 내 활동 기록
GET    /api/users/me/my-ratings/         # 받은 평가
```

---

### 마일리지 & 배지

#### 배지
```
GET    /api/badges/                      # 전체 배지 목록
GET    /api/badges/{id}/                 # 배지 상세
```

#### 활동
```
GET    /api/activities/                  # 활동 카테고리 목록
GET    /api/activities/{id}/             # 활동 상세
```

#### 활동 인증
```
GET    /api/activity-proofs/             # 내 활동 인증 목록
POST   /api/activity-proofs/             # 활동 인증 제출
  {
    "activity": 1,
    "title": "야간 순찰 완료",
    "description": "201동~205동 순찰",
    "proof_image": <file>,
    "duration_hours": 2.0
  }

GET    /api/activity-proofs/{id}/        # 활동 인증 상세
POST   /api/activity-proofs/{id}/approve/  # 활동 승인 (관리자)
POST   /api/activity-proofs/{id}/reject/   # 활동 반려 (관리자)
```

---

### 이웃 온기 (Rating)

```
GET    /api/ratings/                     # 내가 받은 평가
POST   /api/ratings/                     # 평가 남기기
  {
    "rated_user": 2,
    "score": 5,
    "comment": "항상 그룹 활동에 적극 참여해주셨어요!",
    "category": "community"
  }

GET    /api/ratings/{id}/                # 평가 상세
```

---

### 알림

```
GET    /api/notifications/               # 알림 목록 (최신순)
POST   /api/notifications/{id}/mark-as-read/  # 알림 읽음 표시
POST   /api/notifications/mark-all-as-read/   # 모든 알림 읽음 표시
```

---

### 소그룹 & 모임

#### 그룹
```
GET    /api/groups/                      # 그룹 목록
POST   /api/groups/                      # 그룹 생성
  {
    "name": "댕댕이 집사 모임",
    "description": "반려동물을 키우는 주민들의 모임",
    "group_type": "pet",
    "location": "201동 입구",
    "regular_schedule": "매주 토요일 10시",
    "member_limit": 30
  }

GET    /api/groups/{id}/                 # 그룹 상세
PUT    /api/groups/{id}/                 # 그룹 수정
DELETE /api/groups/{id}/                 # 그룹 삭제

POST   /api/groups/{id}/join/            # 그룹 가입
POST   /api/groups/{id}/leave/           # 그룹 탈출
```

#### 번개 (Meetup)
```
GET    /api/meetups/                     # 번개 목록
POST   /api/meetups/                     # 번개 생성
  {
    "title": "일요일 아침 플로깅",
    "description": "함께 달리면서 쓰레기를 줍습시다",
    "location": "아파트 정문",
    "scheduled_at": "2025-01-15T08:00:00Z",
    "duration_minutes": 60,
    "max_participants": 20
  }

GET    /api/meetups/{id}/                # 번개 상세
PUT    /api/meetups/{id}/                # 번개 수정

POST   /api/meetups/{id}/join/           # 번개 참여
POST   /api/meetups/{id}/leave/          # 번개 불참
```

#### 그룹 게시글
```
GET    /api/group-posts/?group_id=1      # 그룹 게시글 목록
POST   /api/group-posts/                 # 게시글 작성
  {
    "group": 1,
    "title": "이번 주 모임 후기",
    "content": "좋은 시간이었습니다...",
    "image": <file>
  }

GET    /api/group-posts/{id}/            # 게시글 상세
PUT    /api/group-posts/{id}/            # 게시글 수정
DELETE /api/group-posts/{id}/            # 게시글 삭제
```

#### 그룹 채팅
```
GET    /api/group-chats/?group_id=1      # 그룹 채팅 메시지 목록
POST   /api/group-chats/                 # 메시지 전송
  {
    "group": 1,
    "message": "안녕하세요!",
    "image": <file>  # 선택사항
  }
```

---

## 🗄️ 데이터 모델

### CustomUser (확장된 사용자 모델)
```python
- username: 사용자명
- email: 이메일
- unit_number: 동호수 (예: 201동 1502호)
- phone_number: 연락처
- profile_image: 프로필 사진
- mileage_points: 마일리지 포인트
- manners_score: 이웃 온기 점수 (0-100)
- current_badges: M2M (현재 활성 배지)
```

### Activity (활동)
```python
- name: 활동 이름
- activity_type: 유형 (patrol/manner/cleaning/helping/event)
- description: 설명
- base_points: 기본 포인트
- points_per_hour: 시간당 포인트
- is_active: 활성 여부
```

### ActivityProof (활동 인증)
```python
- user: FK(CustomUser)
- activity: FK(Activity)
- title: 인증 제목
- description: 설명
- proof_image: 증빙 사진
- duration_hours: 활동 시간
- status: pending/approved/rejected
- points_earned: 획득 포인트
```

### Badge (배지)
```python
- title: 배지명
- description: 설명
- icon: 배지 아이콘
- category: 유형
- required_points: 필요 포인트
- required_activities: 필요 활동 횟수
```

### Rating (평가)
```python
- rater: FK(평가 주는 사람)
- rated_user: FK(평가 받는 사람)
- score: 점수 (1-5)
- comment: 댓글
- category: 평가 범주
```

### Notification (알림)
```python
- recipient: FK(수신자)
- title: 제목
- message: 내용 (LLM 생성)
- notification_type: 유형
- persona: 페르소나
- is_read: 읽음 여부
- is_sent: 발송 여부
```

### Group (소그룹)
```python
- name: 그룹명
- description: 설명
- group_type: 유형 (hobby/pet/sports/volunteer/learning/event)
- creator: FK(생성자)
- members: M2M(GroupMember 통해)
- location: 모임 장소
- regular_schedule: 정기 일정
- member_limit: 인원 제한
```

### Meetup (번개/모임)
```python
- title: 제목
- description: 설명
- creator: FK(생성자)
- participants: M2M
- location: 위치
- scheduled_at: 예정 시간
- duration_minutes: 소요 시간
- max_participants: 최대 참여자
- status: planned/recruiting/confirmed/completed/cancelled
```

---

## 🛠️ 개발 팁

### 테스트 시나리오

#### 1️⃣ 마일리지 & 배지 테스트
```bash
# 1. 활동 인증 제출
POST /api/activity-proofs/
{
  "activity": 1,
  "title": "야간 순찰",
  "description": "201동-205동 순찰",
  "proof_image": <파일>,
  "duration_hours": 2
}

# 2. 관리자로 승인
POST /api/activity-proofs/1/approve/

# 3. 사용자 프로필 확인
GET /api/users/me/
# → mileage_points 증가, 조건 만족 시 배지 자동 지급
```

#### 2️⃣ 이웃 온기 테스트
```bash
# 1. 평가 남기기
POST /api/ratings/
{
  "rated_user": 2,
  "score": 5,
  "comment": "항상 좋은 분위기를 만들어주세요!"
}

# 2. 프로필 확인
GET /api/users/2/
# → manners_score 자동 재계산
```

#### 3️⃣ 소그룹 생성 및 관리
```bash
# 1. 그룹 생성
POST /api/groups/
{
  "name": "러닝 클럽",
  "description": "함께 뛰어요!",
  "group_type": "sports"
}

# 2. 그룹 가입
POST /api/groups/1/join/

# 3. 게시글 작성
POST /api/group-posts/
{
  "group": 1,
  "title": "모임 후기",
  "content": "좋은 시간이었습니다!"
}
```

---

## 📚 추가 리소스

- **Django 공식 문서**: https://docs.djangoproject.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **OpenAI API**: https://platform.openai.com/docs/
- **Anthropic Claude**: https://docs.anthropic.com/

---

## ✨ 다음 단계

### Phase 2 개발 계획
- [ ] 실시간 알림 (WebSocket)
- [ ] 위치 기반 모임 추천 (지도 API)
- [ ] 이미지 AI 분석 (활동 인증 자동화)
- [ ] 모바일 앱 (React Native)
- [ ] 댓글 감정 분석 (악성 댓글 자동 필터)
- [ ] 통계 대시보드

---

**해솔7 커뮤니티팀** 🏘️
