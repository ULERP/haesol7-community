from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUser(AbstractUser):
    unit_number   = models.CharField(max_length=20, blank=True)
    phone_number  = models.CharField(max_length=20, blank=True)
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
    icon                = models.ImageField(upload_to='badges/')
    category            = models.CharField(max_length=20, choices=BADGE_CATEGORY)
    required_points     = models.IntegerField(default=100)
    required_activities = models.IntegerField(default=5)
    is_active           = models.BooleanField(default=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering       = ['category', 'required_points']
        verbose_name_plural = "Badges"

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
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.submitter.username} - {self.activity.name}"


class UserBadge(models.Model):
    user         = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='user_badges')
    badge        = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at    = models.DateTimeField(auto_now_add=True)
    is_displayed = models.BooleanField(default=True)

    class Meta:
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
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering       = ['order']
        verbose_name   = '게시판'
        verbose_name_plural = '게시판 목록'

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

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = '게시글'
        verbose_name_plural = '게시글 목록'

    def __str__(self):
        return self.title


class PostImage(models.Model):
    post  = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='posts/%Y/%m/')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
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
        ordering = ['created_at']

    def __str__(self):
        return f"{self.post.title} 댓글"


class PostLike(models.Model):
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user       = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['post', 'user']]


class Trade(models.Model):
    STATUS_CHOICES = [
        ('available', '판매중/나눔중'),
        ('reserved',  '예약중'),
        ('sold',      '판매완료'),
    ]
    post       = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='trade')
    price      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    currency   = models.CharField(max_length=10, default='KRW')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.post.title} - {self.price}"


class Poll(models.Model):
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='polls')
    question   = models.CharField(max_length=300)
    options    = models.JSONField(default=list, blank=True)
    votes      = models.JSONField(default=dict, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
    created_at         = models.DateTimeField(auto_now_add=True)
    read_at            = models.DateTimeField(blank=True, null=True)

    class Meta:
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
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.question[:50]}"


class ManagementDocument(models.Model):
    title      = models.CharField(max_length=200)
    content    = models.TextField()
    category   = models.CharField(max_length=50)
    embeddings = models.JSONField(blank=True, null=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'title']

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
    members          = models.ManyToManyField('CustomUser', through='GroupMember', related_name='joined_groups')
    group_image      = models.ImageField(upload_to='groups/', blank=True, null=True)
    location         = models.CharField(max_length=200, blank=True)
    regular_schedule = models.CharField(max_length=200, blank=True)
    member_limit     = models.IntegerField(blank=True, null=True)
    is_public        = models.BooleanField(default=True)
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    ROLE_CHOICES = [
        ('member',    '일반 멤버'),
        ('moderator', '운영진'),
        ('leader',    '리더'),
    ]
    group     = models.ForeignKey(Group, on_delete=models.CASCADE)
    user      = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    role      = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
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
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='recruiting')
    thumbnail        = models.ImageField(upload_to='meetups/', blank=True, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return self.title


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
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username} - {self.content[:50]}"


class GroupChat(models.Model):
    group      = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='chat_messages')
    sender     = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='group_messages')
    message    = models.TextField()
    image      = models.ImageField(upload_to='group_chat/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
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
        verbose_name_plural = '회원 등급 목록'

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
        verbose_name_plural = '게시판 등급 권한 목록'

    def __str__(self):
        return f"{self.board.name} — {self.grade.name}"


def get_user_grade(user):
    grade_order = ['총무이사', '분과장', '적극활동대원', '특별활동대원', '봉사활동대원', '입주민']
    user_groups = user.groups.values_list('name', flat=True)
    for grade in grade_order:
        if grade in user_groups:
            return grade
    return '입주민'
