# PROJECT_SPEC.md

## 1. 개요
이 파일은 프로젝트의 유일한 모델 구조(Schema) 정의서입니다. 모든 기능 구현(View, Serializer, Template, API)은 반드시 이 모델 구조를 기반으로 해야 합니다.

## 2. 모델 구조 정의
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# ============================================================================
# ① 마일리지 & 배지 시스템 (Gamification)
# ============================================================================

class CustomUser(AbstractUser):
    """확장된 사용자 모델 - 마일리지, 배지, 온기점수 포함"""
    # 기본 사용자 정보
    unit_number = models.CharField(max_length=20, blank=True, help_text="주민 동호수 (예: 201동 1502호)")
    phone_number = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    introduction = models.TextField(blank=True, max_length=500)
    
    # 마일리지 포인트
    mileage_points = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # 현재 활성 배지
    current_badges = models.ManyToManyField('Badge', blank=True, related_name='users_with_badge')
    
    # 이웃 온기 점수 (0-100)
    manners_score = models.FloatField(default=50.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # 가입일시
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user'
        ordering = ['-created_at']
        app_label = 'core'
    
    def __str__(self):
        # str() 함수로 감싸서 SafeString을 일반 문자열로 확실히 변환합니다.
        return f"{self.username} ({str(self.unit_number)})"


class Badge(models.Model):
    """디지털 배지 정의"""
    BADGE_CATEGORY = [
        ('security', '보안 관련'),
        ('environment', '환경 관련'),
        ('community', '커뮤니티'),
        ('helping', '나눔 관련'),
    ]
    
    title = models.CharField(max_length=50, unique=True)  # 예: "우리 동네 보안관"
    description = models.TextField()
    icon = models.ImageField(upload_to='badges/')
    category = models.CharField(max_length=20, choices=BADGE_CATEGORY)
    
    # 획득 조건
    required_points = models.IntegerField(default=100)  # 필요 포인트
    required_activities = models.IntegerField(default=5)  # 필요 활동 횟수
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'required_points']
        verbose_name_plural = "Badges"
    
    def __str__(self):
        return f"[{self.category}] {self.title}"


class Activity(models.Model):
    """지킴이 활동 카테고리"""
    ACTIVITY_TYPE = [
        ('patrol', '야간 순찰'),
        ('manner', '펫 매너 캠페인'),
        ('cleaning', '환경 정비'),
        ('helping', '이웃 돕기'),
        ('event', '특별 행사'),
    ]
    
    name = models.CharField(max_length=100)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE)
    description = models.TextField()
    points_per_hour = models.IntegerField(default=10)  # 시간당 포인트
    base_points = models.IntegerField(default=50)  # 기본 포인트
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['activity_type', 'name']
    
    def __str__(self):
        return self.name


class ActivityProof(models.Model):
    """활동 인증 기록"""
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('approved', '승인됨'),
        ('rejected', '반려됨'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_proofs')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    proof_image = models.ImageField(upload_to='activity_proofs/')
    duration_hours = models.FloatField(default=1.0)  # 활동 시간
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    points_earned = models.IntegerField(default=0)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(CustomUser, blank=True, null=True, on_delete=models.SET_NULL, related_name='approved_proofs')
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"


class ActivityVerification(models.Model):
    """활동 인증 제출 기록"""
    submitter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_verifications')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='verifications')
    submitted_at = models.DateTimeField(auto_now_add=True)
    activity_date = models.DateField("활동 일시", blank=True, null=True)
    content = models.TextField("활동내용")
    approved = models.BooleanField("담당자 확인", default=False)
    approved_by = models.ForeignKey(CustomUser, blank=True, null=True, on_delete=models.SET_NULL, related_name='activity_verification_approvals')
    approved_at = models.DateTimeField("확인 일시", blank=True, null=True)
    notes = models.TextField("담당자 메모", blank=True)

    class Meta:
        verbose_name = "활동 인증"
        verbose_name_plural = "활동 인증 목록"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.submitter.username} - {self.activity.name} ({'승인됨' if self.approved else '대기중'})"


class UserBadge(models.Model):
    """사용자가 획득한 배지 기록"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    
    earned_at = models.DateTimeField(auto_now_add=True)
    is_displayed = models.BooleanField(default=True)  # 프로필에 표시 여부
    
    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.title}"


# ============================================================================
# ② 이웃 온기 (Manners Score) - CustomUser의 manners_score와 연동
# ============================================================================

class Rating(models.Model):
    """주민 간 평가 (매너평가)"""
    RATING_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]
    
    rater = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ratings_given')
    rated_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ratings_received')
    
    score = models.IntegerField(choices=RATING_CHOICES, default=5)
    comment = models.TextField(max_length=500, blank=True)
    
    # 평가 근거
    category = models.CharField(max_length=20, blank=True)  # 어느 활동에 대한 평가인지
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('rater', 'rated_user')  # 사용자당 1회만 평가 가능
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rater.username} → {self.rated_user.username} ({self.score}⭐)"


# ============================================================================
# ③ 게시판 시스템 (Board)
# ============================================================================

class Board(models.Model):
    """게시판"""
    # final boards:
    # - 공지 및 행정: tags=[지킴이공지, 주민공지, 단지소식, 행정/시책], write_permission='staff'
    # - 우리 동네 소통: tags=[자유, 나눔, 장터, 맛집], write_permission='member'
    # - 생활 정보 공유: tags=[에티켓, 수리보수, 재활용, 육아, 학습, 운동], write_permission='member'
    # - 여가와 활동: tags=[취미, 여행, 영상], write_permission='member'
    # - 지킴이 아카이브: tags=[모집, 활동기록, 회의록, 양식], write_permission='staff'
    # - 건의와 FAQ: tags=[건의, 질문, FAQ], write_permission='member'
    class BoardType(models.TextChoices):
        NOTICE     = 'notice',     '공지사항'
        FREE       = 'free',       '자유게시판'
        VOLUNTEER  = 'volunteer',  '봉사활동'
        ARCHIVE    = 'archive',    '지킴이 아카이브'
        EVENT      = 'event',      '행사/모임'
        SUGGESTION = 'suggestion', '건의/소통'
        GALLERY    = 'gallery',    '갤러리'
        TRADE      = 'trade',      '나눔/장터'
        QNA        = 'qna',        'Q&A'

    PERMISSION_CHOICES = [
        ('all', '전체'),
        ('member', '회원'),
        ('staff', '운영진'),
        ('admin', '관리자'),
    ]

    name = models.CharField(max_length=50)
    board_type = models.CharField(max_length=20, choices=BoardType.choices, default=BoardType.FREE)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-clipboard')
    order = models.PositiveIntegerField(default=0, db_index=True)
    allowed_tags = models.CharField(max_length=200, blank=True, help_text='쉼표로 구분. 예: 공지,질문,건의,회의록')
    write_permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='all', help_text='all/member/staff/admin')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = '게시판'
        verbose_name_plural = '게시판 목록'

    def __str__(self):
        return self.name

    def get_tags_list(self):
        return [t.strip() for t in self.allowed_tags.split(',') if t.strip()]

    def user_can_write(self, user):
        if self.write_permission == 'all':
            return True
        if self.write_permission == 'member':
            return user.is_authenticated
        if self.write_permission == 'staff':
            return user.is_staff or user.groups.filter(name__in=['운영진', 'staff']).exists()
        if self.write_permission == 'admin':
            return user.is_superuser
        return False


class Post(models.Model):
    """게시글"""
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='posts', verbose_name='게시판')
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='posts', verbose_name='작성자')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='posts', verbose_name='카테고리')
    title = models.CharField(max_length=200)
    content = models.TextField()
    tag = models.CharField(max_length=30, blank=True)
    is_pinned = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = '게시글'
        verbose_name_plural = '게시글 목록'

    def __str__(self):
        return f"{self.title} ({self.category})" if self.category else self.title


# ============================================================================
# 게시판 연동 모델 확장: Trade, Poll, Event
# ============================================================================

class Trade(models.Model):
    """장터/나눔 게시글에 연결된 상품 정보"""
    STATUS_CHOICES = [
        ('available', '판매중/나눔중'),
        ('reserved', '예약중'),
        ('sold', '판매완료'),
    ]

    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='trade')
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    currency = models.CharField(max_length=10, default='KRW')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.post.title} - {self.price} {self.currency} ({self.status})"


class Poll(models.Model):
    """게시글에 연결된 설문 (옵션은 Choice 모델로 관리)"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='polls')
    question = models.CharField(max_length=300)
    options = models.JSONField(default=list, blank=True, help_text='옵션 리스트')
    votes = models.JSONField(default=dict, blank=True, help_text='옵션별 투표수 매핑')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


class Event(models.Model):
    """게시글에 연결된 일정 이벤트"""
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='event')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.post.title} @ {self.start_time}"


# ============================================================================
# ④ LLM 기반 에이전트 (동네 에이전트)
# ============================================================================

class Notification(models.Model):
    """알림 메시지 (LLM 기반 친근한 톤)"""
    NOTIFICATION_TYPE = [
        ('activity', '활동 모집'),
        ('announcement', '공지사항'),
        ('badge', '배지 획득'),
        ('community', '커뮤니티'),
        ('event', '행사'),
    ]
    
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    
    title = models.CharField(max_length=200)
    message = models.TextField()  # LLM이 생성한 친근한 메시지
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE)
    persona = models.CharField(max_length=100, blank=True)  # 페르소나 (예: "다정한 아저씨", "친절한 이웃")
    
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    related_activity = models.ForeignKey(Activity, blank=True, null=True, on_delete=models.SET_NULL)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"[{self.notification_type}] {self.title[:50]}"


class ChatHistory(models.Model):
    """챗봇 대화 기록 (RAG 기반 규약 안내)"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='chat_histories')
    
    question = models.TextField()
    answer = models.TextField()  # LLM이 생성한 답변
    
    # RAG 관련
    referenced_documents = models.JSONField(default=list, blank=True)  # 참고한 문서 리스트
    confidence_score = models.FloatField(default=0.0)  # 답변 신뢰도
    
    is_helpful = models.BooleanField(default=True)  # 사용자 피드백
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.question[:50]}"


class ManagementDocument(models.Model):
    """아파트 관리 규약 및 가이드 (RAG를 위한 문서)"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50)  # 예: "주차", "펫", "소음"
    
    embeddings = models.JSONField(blank=True, null=True)  # 벡터 임베딩
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'title']
    
    def __str__(self):
        return f"[{self.category}] {self.title}"


# ============================================================================
# ④ 소그룹 기반 모임 & 번개 (Hyper-Local Meetup)
# ============================================================================

class Group(models.Model):
    """소그룹 (모임)"""
    GROUP_TYPE = [
        ('hobby', '취미 활동'),
        ('pet', '반려동물'),
        ('sports', '스포츠'),
        ('volunteer', '자원봉사'),
        ('learning', '학습'),
        ('event', '정기 행사'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    group_type = models.CharField(max_length=20, choices=GROUP_TYPE)
    
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(CustomUser, through='GroupMember', related_name='joined_groups')
    
    group_image = models.ImageField(upload_to='groups/', blank=True, null=True)
    
    # 모임 장소 정보
    location = models.CharField(max_length=200, blank=True)  # 예: "201동 입구"
    
    # 모임 일정
    regular_schedule = models.CharField(max_length=200, blank=True)  # 예: "매주 토요일 10시"
    
    member_limit = models.IntegerField(blank=True, null=True)  # 인원 제한
    
    is_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def member_count(self):
        return self.members.count()


class GroupMember(models.Model):
    """그룹 멤버"""
    ROLE_CHOICES = [
        ('member', '일반 멤버'),
        ('moderator', '운영진'),
        ('leader', '리더'),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('group', 'user')
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.group.name} - {self.user.username}"


class Meetup(models.Model):
    """번개 (임시 모임 / 특정 행사)"""
    STATUS_CHOICES = [
        ('planned', '계획중'),
        ('recruiting', '모집중'),
        ('confirmed', '확정'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='meetups', blank=True, null=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_meetups')
    participants = models.ManyToManyField(CustomUser, related_name='joined_meetups', blank=True)
    
    location = models.CharField(max_length=200)
    scheduled_at = models.DateTimeField()  # 예정 일시
    duration_minutes = models.IntegerField(default=60)
    
    max_participants = models.IntegerField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='recruiting')
    
    thumbnail = models.ImageField(upload_to='meetups/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_at']
    
    def __str__(self):
        return self.title


class GroupPost(models.Model):
    """그룹 내 게시글"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='group_posts')
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    image = models.ImageField(upload_to='group_posts/', blank=True, null=True)
    
    like_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"[{self.group.name}] {self.title}"


class GroupComment(models.Model):
    """그룹 게시글 댓글"""
    post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='group_comments')
    
    content = models.TextField(max_length=1000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author.username} - {self.content[:50]}"


class GroupChat(models.Model):
    """그룹 채팅 메시지 (실시간 또는 비동기)"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='group_messages')
    
    message = models.TextField()
    
    # 미디어 첨부
    image = models.ImageField(upload_to='group_chat/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.group.name} - {self.sender.username}"
# ============================================================================
# ⑤ 확장 서비스 모델 (Trade, Poll, Event)
# ============================================================================

class Trade(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='trade_info')
    price = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=[('selling', '판매중'), ('sold', '거래완료')], default='selling')

class Poll(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='poll_info')
    question = models.CharField(max_length=200)
    options = models.JSONField(help_text="{'1': '옵션1', '2': '옵션2'}")
    votes = models.JSONField(default=dict)

class Event(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='event_info')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=200)
# ============================================================================
# 업데이트 이력 (2026.05.26)
# ============================================================================

## 3. 추가된 모델

### MemberGrade (회원 등급)
- 6단계 등급: 입주민, 봉사활동대원, 특별활동대원, 적극활동대원, 분과장, 총무이사
- 관리자 페이지에서 추가/수정/삭제 가능
- 자동 등업 조건: required_activities, required_points
- 게시판 기본 권한: can_read_all, can_write, can_comment

### BoardGradePermission (게시판 등급 권한)
- 게시판별 등급 특수 권한 설정
- can_read, can_write, can_comment 개별 설정 가능
- 특수 등급만 열람 가능한 게시판 구현 가능

### Board (게시판)
- board_type: notice/free/volunteer/archive/event/suggestion/gallery/trade/qna
- write_permission: all/member/staff/admin
- allowed_tags: 쉼표 구분 말머리 목록
- 관리자 페이지에서 순서/활성화 관리

### Post (게시글)
- board ForeignKey, tag 말머리, is_pinned 상단고정
- is_anonymous 익명, view_count, like_count

### Comment (댓글)
- parent ForeignKey (대댓글 지원)
- is_anonymous 익명 댓글

### PostLike (좋아요)
- post + user unique_together

## 4. 구현된 기능 목록
- 회원가입/로그인/로그아웃
- 마이페이지 (프로필, 마일리지, 온기점수, 내 게시글/댓글)
- 게시판 목록/상세/말머리 필터
- 게시글 CRUD (작성/수정/삭제/상세)
- 댓글/대댓글
- 좋아요
- 등급별 게시판 권한 체크
- 활동 인증 제출/목록
- 활동 인증 관리자 승인 (포인트 자동 적립)

## 5. 남은 작업
- 게시글 이미지 첨부
- 페이지네이션
- 봉사활동 달력/일정
- 회원 프로필 수정
- 알림 시스템
- RAG 챗봇 (관리 규약 안내)
- PythonAnywhere 배포
