from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUser(AbstractUser):
    unit_number   = models.CharField(max_length=20, blank=True)
    dong          = models.CharField('동', max_length=10, blank=True)
    ho            = models.CharField('호', max_length=10, blank=True)
    security_question = models.CharField('보안 질문', max_length=200, blank=True, default='')
    security_answer   = models.CharField('보안 답변', max_length=100, blank=True, default='')
    nickname      = models.CharField('닉네임', max_length=30, blank=True)
    phone_number  = models.CharField(max_length=20, blank=True)
    is_verified   = models.BooleanField('입주민 인증', default=False)
    verified_at   = models.DateTimeField('인증일시', null=True, blank=True)
    verified_note = models.CharField('인증 메모(관리자용)', max_length=200, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    introduction  = models.TextField(blank=True, max_length=500)
    mileage_points= models.IntegerField(default=0, validators=[MinValueValidator(0)])
    current_badges= models.ManyToManyField('Badge', blank=True, related_name='users_with_badge')
    manners_score = models.FloatField(default=50.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering  = ['-created_at']
        app_label = 'core'
        verbose_name        = '입주민'
        verbose_name_plural = '입주민'

    def __str__(self):
        return f"{self.username} ({str(self.unit_number)})"


class Badge(models.Model):
    BADGE_CATEGORY = [
        ('security',    '보안 관련'),
        ('environment', '환경 관련'),
        ('community',   '커뮤니티'),
        ('helping',     '나눔 관련'),
    ]
    title               = models.CharField(max_length=50, unique=True)
    description         = models.TextField()
    icon                = models.ImageField(upload_to='badges/', blank=True, null=True)
    category            = models.CharField(max_length=20, choices=BADGE_CATEGORY)
    required_points     = models.IntegerField(default=100)
    required_activities = models.IntegerField(default=5)
    is_active           = models.BooleanField(default=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '배지'
        ordering       = ['category', 'required_points']
        verbose_name_plural = '배지'

    def __str__(self):
        return f"[{self.category}] {self.title}"


class Activity(models.Model):
    ACTIVITY_TYPE = [
        ('patrol',   '야간 순찰'),
        ('manner',   '펫 매너 캠페인'),
        ('cleaning', '환경 정비'),
        ('helping',  '이웃 돕기'),
        ('event',    '특별 행사'),
    ]
    name             = models.CharField(max_length=100)
    activity_type    = models.CharField(max_length=20, choices=ACTIVITY_TYPE)
    description      = models.TextField()
    points_per_hour  = models.IntegerField(default=10)
    base_points      = models.IntegerField(default=50)
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['activity_type', 'name']
        verbose_name = '봉사 활동'
        verbose_name_plural = '봉사 활동'

    def __str__(self):
        return self.name


class ActivityProof(models.Model):
    STATUS_CHOICES = [
        ('pending',  '대기중'),
        ('approved', '승인됨'),
        ('rejected', '반려됨'),
    ]
    user           = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='activity_proofs')
    activity       = models.ForeignKey(Activity, on_delete=models.CASCADE)
    title          = models.CharField(max_length=200)
    description    = models.TextField()
    proof_image    = models.ImageField(upload_to='activity_proofs/', blank=True, null=True)
    duration_hours = models.FloatField(default=1.0)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    points_earned  = models.IntegerField(default=0)
    submitted_at   = models.DateTimeField(auto_now_add=True)
    approved_at    = models.DateTimeField(blank=True, null=True)
    approved_by    = models.ForeignKey('CustomUser', blank=True, null=True, on_delete=models.SET_NULL, related_name='approved_proofs')

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = '활동 인증'
        verbose_name_plural = '활동 인증'

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"


class ActivityVerification(models.Model):
    submitter    = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='activity_verifications')
    activity     = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='verifications')
    submitted_at = models.DateTimeField(auto_now_add=True)
    activity_date= models.DateField(blank=True, null=True)
    content      = models.TextField()
    approved     = models.BooleanField(default=False)
    approved_by  = models.ForeignKey('CustomUser', blank=True, null=True, on_delete=models.SET_NULL, related_name='activity_verification_approvals')
    approved_at  = models.DateTimeField(blank=True, null=True)
    notes        = models.TextField(blank=True)

    class Meta:
        verbose_name        = '활동 검증'
        verbose_name_plural = '활동 검증'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.submitter.username} - {self.activity.name}"


class UserBadge(models.Model):
    user         = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='user_badges')
    badge        = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at    = models.DateTimeField(auto_now_add=True)
    is_displayed = models.BooleanField(default=True)

    class Meta:
        verbose_name        = '회원 보유 배지'
        verbose_name_plural = '회원 보유 배지'
        unique_together = ('user', 'badge')
        ordering        = ['-earned_at']

    def __str__(self):
        return f"{self.user.username} - {self.badge.title}"


class Rating(models.Model):
    RATING_CHOICES = [(i, '⭐'*i) for i in range(1, 6)]
    rater      = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='ratings_given')
    rated_user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='ratings_received')
    score      = models.IntegerField(choices=RATING_CHOICES, default=5)
    comment    = models.TextField(max_length=500, blank=True)
    category   = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '이웃 온기 평가'
        verbose_name_plural = '이웃 온기 평가'
        unique_together = ('rater', 'rated_user')
        ordering        = ['-created_at']

    def __str__(self):
        return f"{self.rater.username} → {self.rated_user.username} ({self.score}⭐)"


class Board(models.Model):
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

    LAYOUT_CHOICES = [
        ('list',   '리스트형'),
        ('gallery','사진형'),
        ('card',   '사진설명형'),
        ('market', '중고마켓형'),
    ]

    PERMISSION_CHOICES = [
        ('all',    '전체'),
        ('member', '회원'),
        ('staff',  '운영진'),
        ('admin',  '관리자'),
    ]

    name             = models.CharField(max_length=50)
    board_type       = models.CharField(max_length=20, choices=BoardType.choices, default=BoardType.FREE)
    description      = models.TextField(blank=True)
    icon             = models.CharField(max_length=50, default='fas fa-clipboard')
    order            = models.PositiveIntegerField(default=0, db_index=True)
    allowed_tags     = models.CharField(max_length=200, blank=True)
    write_permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='all')
    layout_type      = models.CharField('레이아웃', max_length=20, choices=LAYOUT_CHOICES, default='list')
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering       = ['order']
        verbose_name   = '게시판'
        verbose_name_plural = '게시판'

    def __str__(self):
        return self.name

    def get_tags_list(self):
        return [t.strip() for t in self.allowed_tags.split(',') if t.strip()]

    def user_can_write(self, user):
        if self.write_permission == 'all':    return True
        if self.write_permission == 'member': return user.is_authenticated
        if self.write_permission == 'staff':  return user.is_staff
        if self.write_permission == 'admin':  return user.is_superuser
        return False


class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    board        = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='posts')
    author       = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, related_name='posts')
    category     = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    title        = models.CharField(max_length=200)
    content      = models.TextField()
    tag          = models.CharField(max_length=30, blank=True)
    is_pinned    = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)
    view_count   = models.PositiveIntegerField(default=0)
    like_count   = models.PositiveIntegerField(default=0)
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    related_posts = models.ManyToManyField('self', blank=True, symmetrical=True, verbose_name='관련 게시글')
    linked_survey = models.ForeignKey('Survey', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_posts', verbose_name='삽입 설문')

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = '📋 게시글'
        verbose_name_plural = '📋 게시글'

    def __str__(self):
        return self.title


class PostImage(models.Model):
    post  = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='posts/%Y/%m/')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name        = '게시글 이미지'
        verbose_name_plural = '게시글 이미지'
        ordering = ['order']


class Comment(models.Model):
    post         = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author       = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, related_name='comments')
    parent       = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content      = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '댓글'
        verbose_name_plural = '댓글'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.post.title} 댓글"


class PostLike(models.Model):
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user       = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '게시글 좋아요'
        verbose_name_plural = '게시글 좋아요'
        unique_together = [['post', 'user']]
class Trade(models.Model):
    STATUS_CHOICES = [
        ('available', '판매중/나눔중'),
        ('reserved',  '예약중'),
        ('sold',      '거래완료'),
    ]
    TRADE_TYPE_CHOICES = [
        ('sell',     '판매'),
        ('share',    '나눔'),
        ('exchange', '교환'),
    ]
    CATEGORY_CHOICES = [
        ('electronics',  '가전/디지털'),
        ('furniture',    '가구/인테리어'),
        ('clothing',     '의류/패션'),
        ('food',         '식품/음료'),
        ('living',       '생활용품'),
        ('books',        '도서/문구'),
        ('sports',       '스포츠/레저'),
        ('kids',         '유아/아동'),
        ('plants',       '식물/원예'),
        ('etc',          '기타'),
    ]
    CONDITION_CHOICES = [
        ('new',       '새상품'),
        ('like_new',  '거의 새것'),
        ('good',      '상태 좋음'),
        ('normal',    '보통'),
        ('bad',       '나쁨'),
    ]
    DELIVERY_CHOICES = [
        ('direct',   '직거래'),
        ('delivery', '택배'),
        ('both',     '직거래+택배'),
    ]
    post          = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='trade')
    trade_type    = models.CharField('거래유형', max_length=20, choices=TRADE_TYPE_CHOICES, default='sell')
    price         = models.DecimalField('가격', max_digits=12, decimal_places=0, default=0)
    status        = models.CharField('거래상태', max_length=20, choices=STATUS_CHOICES, default='available')
    category      = models.CharField('카테고리', max_length=30, choices=CATEGORY_CHOICES, default='etc')
    condition     = models.CharField('상품상태', max_length=20, choices=CONDITION_CHOICES, default='good')
    delivery      = models.CharField('거래방법', max_length=20, choices=DELIVERY_CHOICES, default='direct')
    trade_location = models.CharField('거래장소', max_length=100, blank=True, default='단지 내')
    is_negotiable = models.BooleanField('가격협의', default=True)
    currency      = models.CharField(max_length=10, default='KRW')
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '거래 정보'
        verbose_name_plural = '거래 정보'

    def __str__(self):
        return f"{self.post.title} - {self.get_trade_type_display()} {self.price}원"

    def price_display(self):
        if self.trade_type == 'share':
            return '무료나눔'
        if self.price == 0:
            return '가격협의'
        price_str = f"{int(self.price):,}원"
        if self.is_negotiable:
            price_str += " (협의가능)"
        return price_str


    def __str__(self):
        return f"{self.post.title} - {self.price}"


class Poll(models.Model):
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='polls', null=True, blank=True)
    group      = models.ForeignKey('Group', on_delete=models.CASCADE, related_name='group_polls', null=True, blank=True)
    question   = models.CharField(max_length=300)
    options    = models.JSONField(default=list, blank=True)
    votes      = models.JSONField(default=dict, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '설문조사'
        verbose_name_plural = '설문조사 목록'

    def __str__(self):
        return self.question


class Choice(models.Model):
    poll  = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='choices')
    text  = models.CharField(max_length=200, default='')
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.text


class Event(models.Model):
    post       = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='event')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time   = models.DateTimeField(null=True, blank=True)
    location   = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '봉사 일정'
        verbose_name_plural = '봉사 일정'

    class Meta:
        verbose_name        = '봉사 일정'
        verbose_name_plural = '봉사 일정'

    def __str__(self):
        return f"{self.post.title} @ {self.start_time}"


class Notification(models.Model):
    NOTIFICATION_TYPE = [
        ('activity',     '활동 모집'),
        ('announcement', '공지사항'),
        ('badge',        '배지 획득'),
        ('community',    '커뮤니티'),
        ('event',        '행사'),
    ]
    recipient          = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='notifications')
    title              = models.CharField(max_length=200)
    message            = models.TextField()
    notification_type  = models.CharField(max_length=20, choices=NOTIFICATION_TYPE)
    persona            = models.CharField(max_length=100, blank=True)
    is_read            = models.BooleanField(default=False)
    is_sent            = models.BooleanField(default=False)
    related_activity   = models.ForeignKey(Activity, blank=True, null=True, on_delete=models.SET_NULL)
    link               = models.CharField(max_length=200, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    read_at            = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name        = '알림'
        verbose_name_plural = '알림'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title[:50]}"


class ChatHistory(models.Model):
    user                  = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='chat_histories')
    question              = models.TextField()
    answer                = models.TextField()
    referenced_documents  = models.JSONField(default=list, blank=True)
    confidence_score      = models.FloatField(default=0.0)
    is_helpful            = models.BooleanField(default=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '채팅 기록'
        verbose_name_plural = '채팅 기록'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.question[:50]}"


class ManagementDocument(models.Model):
    CATEGORY_CHOICES = [
        ('공지',   '공지사항'),
        ('규정',   '규정/내규'),
        ('회의록', '회의록'),
        ('예산',   '예산/결산'),
        ('계획',   '연간계획'),
        ('기타',   '기타'),
    ]
    title      = models.CharField('제목', max_length=200)
    content    = models.TextField('내용', blank=True)
    category   = models.CharField('카테고리', max_length=50, choices=CATEGORY_CHOICES, default='기타')
    file       = models.FileField('첨부파일', upload_to='docs/', blank=True, null=True)
    author     = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='작성자')
    view_count = models.PositiveIntegerField('조회수', default=0)
    embeddings = models.JSONField('임베딩', blank=True, null=True)
    is_active  = models.BooleanField('활성화', default=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        ordering = ['category', 'title']
        verbose_name = '관리 문서'
        verbose_name_plural = '관리 문서'

    def __str__(self):
        return f"[{self.category}] {self.title}"


class Group(models.Model):
    GROUP_TYPE = [
        ('hobby',     '취미 활동'),
        ('pet',       '반려동물'),
        ('sports',    '스포츠'),
        ('volunteer', '자원봉사'),
        ('learning',  '학습'),
        ('event',     '정기 행사'),
    ]
    name             = models.CharField(max_length=100)
    description      = models.TextField()
    group_type       = models.CharField(max_length=20, choices=GROUP_TYPE)
    creator          = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='created_groups')
    members          = models.ManyToManyField('CustomUser', through='GroupMember', through_fields=('group','user'), related_name='joined_groups')
    group_image      = models.ImageField(upload_to='groups/', blank=True, null=True)
    location         = models.CharField(max_length=200, blank=True)
    regular_schedule = models.CharField(max_length=200, blank=True)
    member_limit     = models.IntegerField(blank=True, null=True)
    JOIN_TYPE = [
        ('open',    '자유가입'),
        ('approve', '승인제'),
        ('invite',  '초대제'),
    ]
    STATUS_CHOICES = [
        ('active',   '운영중'),
        ('pending',  '승인대기'),  # 10인 이상 생성시
        ('dissolving','해체투표중'),
        ('dissolved','해체됨'),
    ]
    join_type        = models.CharField('가입방식', max_length=20, choices=JOIN_TYPE, default='open')
    status           = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='active')
    is_public        = models.BooleanField(default=True)
    is_active        = models.BooleanField(default=True)
    is_limited       = models.BooleanField('기간한정', default=False)
    expires_at       = models.DateTimeField('해체예정일', null=True, blank=True)
    dissolve_vote_at = models.DateTimeField('해체투표시작', null=True, blank=True)
    approved_by      = models.ForeignKey('CustomUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_groups', verbose_name='승인자')
    approved_at      = models.DateTimeField('승인일시', null=True, blank=True)
    emblem_level     = models.PositiveIntegerField('엠블럼 레벨', default=1)
    activity_score   = models.PositiveIntegerField('활동점수', default=0)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def member_count(self):
        return self.groupmember_set.filter(is_active=True).count()

    def needs_admin_approval(self):
        return self.member_limit and self.member_limit >= 10

    class Meta:
        ordering = ['-created_at']
        verbose_name = '🤝 소모임'
        verbose_name_plural = '🤝 소모임'

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    ROLE_CHOICES = [
        ('member',    '일반 멤버'),
        ('moderator', '운영진'),
        ('leader',    '리더'),
    ]
    JOIN_STATUS = [
        ('pending',  '가입대기'),
        ('invited',  '초대됨'),
        ('approved', '승인됨'),
        ('rejected', '거절됨'),
        ('banned',   '강제퇴장'),
    ]
    group       = models.ForeignKey(Group, on_delete=models.CASCADE)
    user        = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    role        = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    join_status = models.CharField('가입상태', max_length=20, choices=JOIN_STATUS, default='approved')
    joined_at   = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('CustomUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_members')
    ban_reason  = models.TextField('퇴장사유', blank=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        verbose_name        = '소모임 회원'
        verbose_name_plural = '소모임 회원'
        unique_together = ('group', 'user')
        ordering        = ['-joined_at']

    def __str__(self):
        return f"{self.group.name} - {self.user.username}"


class Meetup(models.Model):
    STATUS_CHOICES = [
        ('planned',   '계획중'),
        ('recruiting','모집중'),
        ('confirmed', '확정'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]
    group            = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='meetups', blank=True, null=True)
    title            = models.CharField(max_length=200)
    description      = models.TextField()
    creator          = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='created_meetups')
    participants     = models.ManyToManyField('CustomUser', related_name='joined_meetups', blank=True)
    location         = models.CharField(max_length=200)
    scheduled_at     = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=60)
    max_participants = models.IntegerField(blank=True, null=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    min_participants = models.IntegerField(default=2, verbose_name='최소 인원')
    avg_rating       = models.FloatField(default=0.0, verbose_name='평균 평점')
    rating_count     = models.IntegerField(default=0, verbose_name='평가 수')
    is_confirmed     = models.BooleanField(default=False, verbose_name='관리자 승인')
    confirmed_by     = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_meetups')
    confirmed_at     = models.DateTimeField(null=True, blank=True)
    result_note      = models.TextField(blank=True, verbose_name='활동 결과')
    thumbnail        = models.ImageField(upload_to='meetups/', blank=True, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at']
        verbose_name = '번개/모임'
        verbose_name_plural = '번개/모임'

    def __str__(self):
        return self.title




class MeetupRating(models.Model):
    """봉사활동 평가"""
    meetup     = models.ForeignKey(Meetup, on_delete=models.CASCADE, related_name='ratings')
    rater      = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='meetup_ratings')
    score      = models.IntegerField(choices=[(i,i) for i in range(1,6)], verbose_name='평점')
    comment    = models.TextField(blank=True, verbose_name='한마디')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('meetup', 'rater')
        verbose_name = '봉사활동 평가'
        verbose_name_plural = '봉사활동 평가'

    def __str__(self):
        return f"{self.meetup.title} - {self.rater.nickname} ({self.score}점)"
class GroupPost(models.Model):
    group         = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts')
    author        = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='group_posts')
    title         = models.CharField(max_length=200)
    content       = models.TextField()
    image         = models.ImageField(upload_to='group_posts/', blank=True, null=True)
    like_count    = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = '소모임 게시글'
        verbose_name_plural = '소모임 게시글'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.group.name}] {self.title}"


class GroupComment(models.Model):
    post       = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='comments')
    author     = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='group_comments')
    content    = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = '소모임 댓글'
        verbose_name_plural = '소모임 댓글'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username} - {self.content[:50]}"



class GroupLeaderLog(models.Model):
    """방장 활동 기록"""
    ACTION_CHOICES = [
        ('create',   '소모임 생성'),
        ('approve',  '가입 승인'),
        ('reject',   '가입 거절'),
        ('ban',      '강제 퇴장'),
        ('invite',   '초대'),
        ('delegate', '방장 위임'),
        ('dissolve', '해체 신청'),
        ('edit',     '소모임 수정'),
        ('admin_change', '관리자 변경'),
    ]
    group      = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='leader_logs')
    actor      = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='leader_actions')
    target     = models.ForeignKey('CustomUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='leader_action_targets')
    action     = models.CharField(max_length=20, choices=ACTION_CHOICES)
    detail     = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '🤝 방장 활동 기록'
        verbose_name_plural = '🤝 방장 활동 기록'

    def __str__(self):
        return f"[{self.get_action_display()}] {self.actor} → {self.group.name}"


class GroupDissolveVote(models.Model):
    """소모임 해체 투표 (5인 이상)"""
    group      = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='dissolve_vote')
    started_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='dissolve_votes')
    started_at = models.DateTimeField(auto_now_add=True)
    ends_at    = models.DateTimeField()
    oppose_users = models.ManyToManyField('CustomUser', blank=True, related_name='opposed_dissolves')

    class Meta:
        verbose_name = '🤝 해체 투표'
        verbose_name_plural = '🤝 해체 투표'

    def oppose_count(self):
        return self.oppose_users.count()

    def is_blocked(self):
        total = self.group.member_count()
        return self.oppose_count() > total / 2

    def __str__(self):
        return f"{self.group.name} 해체투표"

class GroupChat(models.Model):
    group      = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='chat_messages')
    sender     = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='group_messages')
    message    = models.TextField(blank=True)
    image      = models.ImageField(upload_to='group_chat/', blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_pinned  = models.BooleanField(default=False)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '소모임 채팅'
        verbose_name_plural = '소모임 채팅'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.group.name} - {self.sender.username}"


class MemberGrade(models.Model):
    BADGE_COLOR_CHOICES = [
        ('secondary', '회색'),
        ('primary',   '파랑'),
        ('success',   '초록'),
        ('info',      '하늘'),
        ('warning',   '노랑'),
        ('danger',    '빨강'),
        ('dark',      '검정'),
    ]
    name                = models.CharField(max_length=30, unique=True)
    description         = models.TextField(blank=True)
    order               = models.PositiveIntegerField(default=0, db_index=True)
    badge_color         = models.CharField(max_length=20, choices=BADGE_COLOR_CHOICES, default='secondary')
    icon                = models.CharField(max_length=50, default='fas fa-user')
    auto_upgrade        = models.BooleanField(default=False)
    required_activities = models.PositiveIntegerField(default=0)
    required_points     = models.PositiveIntegerField(default=0)
    can_read_all        = models.BooleanField(default=True)
    can_write           = models.BooleanField(default=True)
    can_comment         = models.BooleanField(default=True)
    is_active           = models.BooleanField(default=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ['order']
        verbose_name        = '회원 등급'
        verbose_name_plural = '회원 등급'

    def __str__(self):
        return f"[{self.order}] {self.name}"


class BoardGradePermission(models.Model):
    board       = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='grade_permissions')
    grade       = models.ForeignKey(MemberGrade, on_delete=models.CASCADE, related_name='board_permissions')
    can_read    = models.BooleanField(default=True)
    can_write   = models.BooleanField(default=False)
    can_comment = models.BooleanField(default=True)

    class Meta:
        unique_together     = [['board', 'grade']]
        verbose_name        = '게시판 등급 권한'
        verbose_name_plural = '게시판 등급 권한'

    def __str__(self):
        return f"{self.board.name} — {self.grade.name}"


def get_user_grade(user):
    grade_order = ['총무이사', '분과장', '적극활동대원', '특별활동대원', '봉사활동대원', '입주민']
    user_groups = user.groups.values_list('name', flat=True)
    for grade in grade_order:
        if grade in user_groups:
            return grade
    return '입주민'


class DirectMessage(models.Model):
    """1:1 개인 채팅"""
    sender    = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='sent_messages')
    receiver  = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='received_messages')
    message   = models.TextField(blank=True)
    image     = models.ImageField(upload_to='dm/', blank=True, null=True)
    is_read   = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = '1:1 메시지'
        verbose_name_plural = '1:1 메시지'

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.message[:30]}"


class PublicChat(models.Model):
    """단지 전체 오픈 채팅방"""
    author    = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='public_chats')
    message   = models.TextField(blank=True)
    image     = models.ImageField(upload_to='public_chat/', blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = '오픈채팅'
        verbose_name_plural = '오픈채팅'

    def __str__(self):
        return f"{self.author.username}: {self.message[:30]}"


# ============================================================================
# 설문조사 시스템
# ============================================================================
class Survey(models.Model):
    SURVEY_TYPE = [
        ('single', '단일 선택'),
        ('multiple', '복수 선택'),
        ('text', '주관식'),
        ('rating', '평점 (1-5점)'),
    ]
    STATUS = [
        ('draft', '작성중'),
        ('active', '진행중'),
        ('closed', '마감'),
    ]
    title       = models.CharField('설문 제목', max_length=200)
    description = models.TextField('설명', blank=True)
    creator     = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='surveys')
    survey_type = models.CharField('유형', max_length=20, choices=SURVEY_TYPE, default='single')
    status      = models.CharField('상태', max_length=20, choices=STATUS, default='active')
    is_anonymous = models.BooleanField('익명 응답', default=True)
    allow_multiple = models.BooleanField('중복 응답 허용', default=False)
    ends_at     = models.DateTimeField('마감일', null=True, blank=True)
    source_post = models.ForeignKey('Post', on_delete=models.SET_NULL, null=True, blank=True, related_name='surveys', verbose_name='원본 게시글')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '⚙️ 설문조사'
        verbose_name_plural = '⚙️ 설문조사'

    def __str__(self):
        return self.title

    @property
    def total_responses(self):
        return self.responses.count()

    @property
    def is_active(self):
        from django.utils import timezone
        if self.status != 'active':
            return False
        if self.ends_at and self.ends_at < timezone.now():
            return False
        return True


class SurveyQuestion(models.Model):
    QUESTION_TYPE = [
        ('single',   '단일 선택'),
        ('multiple', '복수 선택'),
        ('text',     '주관식'),
        ('rating',   '평점 (1-5점)'),
        ('scale',    '선형 척도 (슬라이더)'),
        ('date',     '날짜 선택'),
        ('daterange','날짜 범위 선택'),
        ('rank',     '순위 매기기'),
        ('matrix',   '매트릭스/표'),
        ('section',  '섹션 구분'),
    ]
    survey        = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text          = models.CharField('질문', max_length=300)
    description   = models.CharField('질문 설명', max_length=300, blank=True)
    question_type = models.CharField('유형', max_length=20, choices=QUESTION_TYPE, default='single')
    options       = models.JSONField('선택지', default=list, blank=True)
    rows          = models.JSONField('행 (매트릭스용)', default=list, blank=True)
    scale_min     = models.IntegerField('최솟값', default=1)
    scale_max     = models.IntegerField('최댓값', default=10)
    scale_min_label = models.CharField('최솟값 레이블', max_length=50, blank=True)
    scale_max_label = models.CharField('최댓값 레이블', max_length=50, blank=True)
    is_required   = models.BooleanField('필수', default=True)
    order         = models.PositiveIntegerField('순서', default=0)

    class Meta:
        ordering = ['order']
        verbose_name = '설문 질문'

    def __str__(self):
        return f"{self.survey.title} - {self.text[:30]}"


class SurveyResponse(models.Model):
    survey      = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    respondent  = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='survey_responses')
    answers     = models.JSONField('응답', default=dict)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = '설문 응답'

    def __str__(self):
        return f"{self.survey.title} - {self.respondent.username if self.respondent else '익명'}"


# ============================================================================
# 채팅 미니 투표
# ============================================================================
class ChatPoll(models.Model):
    """채팅창 내 /투표 명령어로 생성되는 미니 투표"""
    chat_type   = models.CharField(max_length=20, default='public')  # public/group/dm
    group       = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, related_name='polls')
    creator     = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='chat_polls')
    question    = models.CharField('질문', max_length=200)
    options     = models.JSONField('선택지', default=list)
    votes       = models.JSONField('투표 결과', default=dict)  # {option: [user_id, ...]}
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '채팅 투표'

    def __str__(self):
        return f"{self.question[:30]}"

    @property
    def total_votes(self):
        return sum(len(v) for v in self.votes.values())

    def get_results(self):
        total = self.total_votes
        results = []
        for opt in self.options:
            voters = self.votes.get(opt, [])
            cnt = len(voters)
            pct = round(cnt/total*100) if total > 0 else 0
            results.append({'option': opt, 'count': cnt, 'percent': pct, 'voters': voters})
        return results

class Letter(models.Model):
    """쪽지 (받은쪽지함 / 보낸쪽지함 이원화)"""
    sender   = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='sent_letters',     verbose_name='보낸 사람')
    receiver = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='received_letters', verbose_name='받는 사람')
    subject  = models.CharField(max_length=100, verbose_name='제목')
    content  = models.TextField(verbose_name='내용')
    parent   = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies', verbose_name='원본 쪽지')
    is_read          = models.BooleanField(default=False)
    sender_deleted   = models.BooleanField(default=False)
    receiver_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '쪽지'
        verbose_name_plural = '쪽지'

    def __str__(self):
        return f"[{self.subject}] {self.sender} → {self.receiver}"



class Complaint(models.Model):
    """민원/건의 접수"""
    STATUS = [
        ('received',  '접수됨'),
        ('reviewing', '검토중'),
        ('done',      '처리완료'),
        ('rejected',  '반려'),
    ]
    CATEGORY = [
        ('noise',     '소음'),
        ('parking',   '주차'),
        ('facility',  '시설'),
        ('cleaning',  '청소/위생'),
        ('security',  '보안/안전'),
        ('delivery',  '택배'),
        ('etc',       '기타'),
    ]
    author      = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='complaints')
    category    = models.ForeignKey('ComplaintCategory', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='분류')
    title       = models.CharField(max_length=100)
    content     = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    status      = models.CharField(max_length=20, choices=STATUS, default='received')
    admin_reply = models.TextField(blank=True)
    replied_at  = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '민원/건의'
        verbose_name_plural = '민원/건의'

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"


class Notice(models.Model):
    """주차/택배/긴급 빠른 공지"""
    TYPE = [
        ('parking',   '주차 안내'),
        ('delivery',  '택배 안내'),
        ('urgent',    '긴급 공지'),
        ('general',   '일반 공지'),
        ('water',     '단수/정전'),
    ]
    author      = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='notices')
    notice_type = models.ForeignKey('NoticeCategory', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='유형')
    title       = models.CharField(max_length=100)
    content     = models.TextField()
    is_pinned   = models.BooleanField(default=False)
    expires_at  = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = '빠른 공지'
        verbose_name_plural = '빠른 공지'

    def __str__(self):
        return f"[{self.get_notice_type_display()}] {self.title}"


class ComplaintCategory(models.Model):
    """민원 분류 (관리자가 동적으로 추가/삭제)"""
    name       = models.CharField(max_length=30, unique=True, verbose_name='분류명')
    icon       = models.CharField(max_length=30, default='bi-tag', verbose_name='Bootstrap 아이콘 클래스')
    order      = models.PositiveIntegerField(default=0, verbose_name='정렬순서')
    is_active  = models.BooleanField(default=True, verbose_name='활성화')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = '민원 분류'
        verbose_name_plural = '민원 분류'

    def __str__(self):
        return self.name


class NoticeCategory(models.Model):
    """공지 유형 (관리자가 동적으로 추가/삭제)"""
    name       = models.CharField(max_length=30, unique=True, verbose_name='유형명')
    icon       = models.CharField(max_length=30, default='bi-bell', verbose_name='Bootstrap 아이콘 클래스')
    color      = models.CharField(max_length=20, default='secondary', verbose_name='배지 색상(Bootstrap)')
    order      = models.PositiveIntegerField(default=0, verbose_name='정렬순서')
    is_active  = models.BooleanField(default=True, verbose_name='활성화')

    class Meta:
        ordering = ['order', 'name']
        verbose_name = '공지 유형'
        verbose_name_plural = '공지 유형'

    def __str__(self):
        return self.name


class CalendarEvent(models.Model):
    TYPE_CHOICES = [
        ('personal',  '개인'),
        ('volunteer', '봉사'),
        ('event',     '단지행사'),
        ('group',     '소모임'),
    ]
    # 공개범위:
    #   private        = 나만보기 (즉시적용)
    #   group_pending  = 소모임공개 승인대기 (소모임장 승인 필요)
    #   group          = 소모임공개 (승인완료)
    #   pending        = 전체공개 승인대기 (관리자 승인 필요)
    #   public         = 전체공개 (승인완료)
    VISIBILITY_CHOICES = [
        ('private',       '나만보기'),
        ('group_pending', '소모임공개(승인대기)'),
        ('group',         '소모임공개'),
        ('pending',       '전체공개(승인대기)'),
        ('public',        '전체공개'),
    ]
    title        = models.CharField('제목', max_length=200)
    description  = models.TextField('내용', blank=True)
    event_type   = models.CharField('종류', max_length=20, choices=TYPE_CHOICES, default='event')
    start_time   = models.DateTimeField('시작')
    end_time     = models.DateTimeField('종료', null=True, blank=True)
    location     = models.CharField('장소', max_length=200, blank=True)
    creator      = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='calendar_events', verbose_name='작성자')
    group        = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='calendar_events', verbose_name='소모임')
    visibility   = models.CharField('공개범위', max_length=20, choices=VISIBILITY_CHOICES, default='private')
    # 승인 (관리자)
    is_approved  = models.BooleanField('관리자승인', default=False)
    approved_by  = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_events', verbose_name='승인자')
    approved_at  = models.DateTimeField('승인일시', null=True, blank=True)
    # 소모임장 승인
    group_approved_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='group_approved_events', verbose_name='소모임장승인자')
    group_approved_at = models.DateTimeField('소모임장승인일시', null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    # 반복 일정 (RRule 방식 - DB에 규칙만 저장, 인스턴스는 프론트에서 생성)
    # 예: "FREQ=WEEKLY;INTERVAL=1;UNTIL=20261231T000000Z"
    rrule          = models.TextField('반복규칙(RRule)', blank=True)
    recur_interval = models.PositiveSmallIntegerField('반복간격', default=1)

    class Meta:
        ordering = ['start_time']
        verbose_name = '📅 캘린더 일정'
        verbose_name_plural = '📅 캘린더 일정'

    def __str__(self):
        return f"[{self.get_event_type_display()}] {self.title}"


class SiteConfig(models.Model):
    hero_image   = models.ImageField('히어로 배경사진', upload_to='site/', blank=True, null=True)
    hero_color   = models.CharField('히어로 배경색', max_length=20, default='#1a7a4a')
    site_name    = models.CharField('단지명', max_length=100, default='해솔마을 7단지 지킴이')
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '사이트 설정'
        verbose_name_plural = '사이트 설정'

    def __str__(self):
        return '사이트 설정'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj



class UserFollow(models.Model):
    """팔로우 (단방향) — 맞팔 시 친구 관계"""
    follower   = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='following')
    following  = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']
        verbose_name = '👥 팔로우'
        verbose_name_plural = '👥 팔로우'

    def __str__(self):
        return f"{self.follower.username} → {self.following.username}"

    @classmethod
    def is_friend(cls, user_a, user_b):
        """맞팔 여부 확인"""
        return (cls.objects.filter(follower=user_a, following=user_b).exists() and
                cls.objects.filter(follower=user_b, following=user_a).exists())

    @classmethod
    def get_friends(cls, user):
        """맞팔 친구 목록"""
        following_ids = cls.objects.filter(follower=user).values_list('following_id', flat=True)
        follower_ids  = cls.objects.filter(following=user).values_list('follower_id', flat=True)
        friend_ids = set(following_ids) & set(follower_ids)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(pk__in=friend_ids)

class AdminActionLog(models.Model):
    """관리자 행위 로그 — 개인정보보호법 29조 안전조치 의무"""
    ACTION_CHOICES = [
        ('pw_reset',     '비밀번호 초기화'),
        ('grade_change', '등급 변경'),
        ('activate',     '계정 활성화'),
        ('deactivate',   '계정 비활성화'),
        ('verify',       '입주민 인증 승인'),
        ('reject',       '입주민 인증 거절'),
    ]
    admin       = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL,
                    null=True, related_name='admin_actions')
    target_user = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL,
                    null=True, related_name='admin_action_targets')
    action      = models.CharField(max_length=20, choices=ACTION_CHOICES)
    detail      = models.TextField(blank=True)   # 평문 비밀번호 절대 저장 금지
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '관리자 행위 로그'
        verbose_name_plural = '관리자 행위 로그'

    def __str__(self):
        return f"[{self.get_action_display()}] {self.admin} → {self.target_user} ({self.created_at:%Y-%m-%d %H:%M})"
