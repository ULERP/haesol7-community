from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from rest_framework import viewsets
from rest_framework.response import Response
from .models import (
    Activity, ActivityProof, Post, Group, Meetup,
    Board, Comment, PostLike, CustomUser,
    MemberGrade, BoardGradePermission
)
from .serializers import PostSerializer, GroupSerializer, MeetupSerializer


# ============================================================================
# 권한 헬퍼
# ============================================================================
def get_user_grade(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return MemberGrade.objects.order_by('-order').first()
    grade_names = user.groups.values_list('name', flat=True)
    return MemberGrade.objects.filter(
        name__in=grade_names, is_active=True
    ).order_by('-order').first()

def check_board_permission(user, board, action='read'):
    """
    게시판 권한 체크
    write_permission: all / member / staff / admin
    읽기: 비로그인 → False, 로그인 → True (티저는 뷰에서 별도 처리)
    쓰기/댓글: board.write_permission 기준
    MemberGrade/BoardGradePermission 고급 설정이 있으면 그걸 우선 적용
    """
    # 슈퍼유저 전체 허용
    if user.is_authenticated and user.is_superuser:
        return True

    # 읽기 권한
    if action == 'read':
        if board.write_permission == 'admin':
            return user.is_authenticated and (user.is_staff or user.is_superuser)
        if board.write_permission == 'staff':
            return user.is_authenticated and user.is_staff
        # 일반 게시판: 로그인 + 인증 필요
        return user.is_authenticated and (getattr(user, 'is_verified', False) or user.is_staff)

    # 쓰기/댓글 권한 — MemberGrade 고급설정 우선
    if user.is_authenticated:
        user_grade = get_user_grade(user)
        if user_grade:
            perm = BoardGradePermission.objects.filter(board=board, grade=user_grade).first()
            if perm:
                if action == 'write':   return perm.can_write
                if action == 'comment': return perm.can_comment

    # 기본 write_permission 기반
    if board.write_permission == 'all':
        return user.is_authenticated and (getattr(user, 'is_verified', False) or user.is_staff)
    if board.write_permission == 'member':
        return user.is_authenticated and (getattr(user, 'is_verified', False) or user.is_staff)
    if board.write_permission == 'staff':
        return user.is_authenticated and user.is_staff
    if board.write_permission == 'admin':
        return user.is_authenticated and user.is_superuser
    return False


# ============================================================================
# 메인
# ============================================================================
def index(request):
    from .models import ManagementDocument, Post, Board
    from django.contrib.auth import get_user_model
    User = get_user_model()
    # 공지 게시판 글
    try:
        notice_board = Board.objects.filter(board_type='notice', is_active=True).first()
        notice_posts = Post.objects.filter(board=notice_board, is_active=True).order_by('-created_at')[:3] if notice_board else []
    except: notice_posts = []
    # 관리 문서
    try: recent_docs = ManagementDocument.objects.filter(is_active=True).order_by('-updated_at')[:3]
    except: recent_docs = []
    # 전체 입주민
    try: all_users = User.objects.filter(is_active=True).exclude(id=request.user.id if request.user.is_authenticated else 0).order_by('username')[:30]
    except: all_users = []
    # 온라인 입주민 (최근 5분 이내 - 간단히 최근 가입자로 대체)
    try: online_users = User.objects.filter(is_active=True).order_by('-last_login')[:8]
    except: online_users = []
    # 내 소모임
    try:
        from .models import Group
        my_groups = Group.objects.filter(members=request.user, is_active=True)[:5] if request.user.is_authenticated else []
    except: my_groups = []

    boards = Board.objects.filter(is_active=True).order_by('order')
    active_boards = boards.exclude(board_type__in=['trade','qna','gallery','faq','complaint']).exclude(name__in=['FAQ','나눔/장터','민원/오류','민원·건의'])
    recent_posts = Post.objects.filter(is_active=True).order_by('-created_at')[:10]
    upcoming_events = Activity.objects.filter(is_active=True).order_by('created_at')[:5]
    from .models import Badge, ActivityProof, Meetup
    activities_count = Activity.objects.filter(is_active=True).count()
    approved_activities_count = ActivityProof.objects.filter(status='approved').count()
    badges_count = Badge.objects.filter(is_active=True).count()
    upcoming_meetups = Meetup.objects.filter(status='recruiting').order_by('scheduled_at')[:3]
    groups_count = Group.objects.filter(is_active=True).count()
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    from .models import PostLike, Survey, Poll, PublicChat, Notice, Event

    now = timezone.now()
    week_ago = now - timedelta(days=7)

    # 인기 게시글 (최근 7일, 좋아요 많은 순)
    hot_posts = Post.objects.filter(
        is_active=True, created_at__gte=week_ago
    ).order_by('-like_count', '-created_at')[:5]

    # 진행중인 설문 (status: draft/active/closed)
    try:
        active_surveys = Survey.objects.filter(
            status='active'
        ).annotate(resp_count=Count('responses')).order_by('-resp_count')[:3]
    except: active_surveys = []

    # 진행중인 채팅 투표
    try:
        active_polls = Poll.objects.filter(
            is_active=True
        ).order_by('-created_at')[:3]
    except: active_polls = []

    # 최근 공지
    try:
        recent_notices = Notice.objects.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=now)
        ).order_by('-is_pinned', '-created_at')[:3]
    except: recent_notices = []

    # 최근 채팅 (미리보기용)
    try:
        recent_chats = PublicChat.objects.filter(
            is_active=True
        ).select_related('author').order_by('-created_at')[:5]
    except: recent_chats = []

    # 봉사 일정
    try:
        upcoming_volunteer = Event.objects.filter(
            start_time__gte=now
        ).order_by('start_time')[:3]
    except: upcoming_volunteer = []

    # 단지 현황 숫자
    from django.contrib.auth import get_user_model
    User2 = get_user_model()
    from .models import SiteConfig as SC
    site_cfg = SC.get()
    from .models import SiteConfig as SC
    site_cfg = SC.get()
    total_users    = User2.objects.filter(is_active=True).count()
    verified_users = User2.objects.filter(is_active=True, is_verified=True).count()

    # 월별 봉사 활동 통계 (최근 6개월)
    import json as _json
    monthly_stats = []
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end   = (month_start + timedelta(days=32)).replace(day=1)
        count = ActivityProof.objects.filter(
            status='approved',
            submitted_at__gte=month_start,
            submitted_at__lt=month_end
        ).count()
        monthly_stats.append({'month': month_start.strftime('%m월'), 'count': count})

    # 소모임 유형별 현황
    from .models import Group as GroupModel
    group_type_stats = list(GroupModel.objects.filter(is_active=True).values('group_type').annotate(cnt=Count('group_type')).order_by('-cnt'))
    group_type_labels = {'hobby':'취미','pet':'반려동물','sports':'스포츠','volunteer':'봉사','learning':'학습','event':'행사'}
    for g in group_type_stats:
        g['label'] = group_type_labels.get(g['group_type'], g['group_type'])

    return render(request, 'index.html', {
        'boards': boards,
        'active_boards': active_boards,
        'recent_posts': recent_posts,
        'hot_posts': hot_posts,
        'upcoming_events': upcoming_events,
        'notice_posts': notice_posts,
        'recent_docs': recent_docs,
        'all_users': all_users,
        'online_users': online_users,
        'my_groups': my_groups,
        'activities_count': activities_count,
        'approved_activities_count': approved_activities_count,
        'badges_count': badges_count,
        'upcoming_meetups': upcoming_meetups,
        'groups_count': groups_count,
        'active_surveys': active_surveys,
        'active_polls': active_polls,
        'recent_notices': recent_notices,
        'recent_chats': recent_chats,
        'upcoming_volunteer': upcoming_volunteer,
        'hero_image': site_cfg.hero_image.url if site_cfg.hero_image else None,
        'hero_color': site_cfg.hero_color,
        'hero_image': site_cfg.hero_image.url if site_cfg.hero_image else None,
        'hero_color': site_cfg.hero_color,
        'total_users': total_users,
        'verified_users': verified_users,
        'monthly_stats_json': _json.dumps(monthly_stats, ensure_ascii=False),
        'group_type_stats_json': _json.dumps(group_type_stats, ensure_ascii=False),
    })


# ============================================================================
# 회원
# ============================================================================
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active or user.is_superuser:
                auth_login(request, user)
                return redirect('index')
            else:
                messages.error(request, '관리자 승인 대기 중입니다.')
        else:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
    return render(request, 'registration/login.html')

def signup(request):
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        real_name = request.POST.get('real_name', '').strip()
        nickname  = request.POST.get('nickname', '').strip()
        dong      = request.POST.get('dong', '').strip()
        ho        = request.POST.get('ho', '').strip()
        phone     = request.POST.get('phone', '').strip()
        email     = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 != password2:
            messages.error(request, '비밀번호가 일치하지 않습니다.')
            return render(request, 'registration/signup.html')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, '이미 사용 중인 아이디입니다.')
            return render(request, 'registration/signup.html')
        if nickname and CustomUser.objects.filter(nickname=nickname).exists():
            messages.error(request, '이미 사용 중인 닉네임입니다.')
            return render(request, 'registration/signup.html')
        # 닉네임 미입력 시 아이디로 자동 설정
        if not nickname:
            nickname = username
        user = CustomUser.objects.create_user(
            username=username,
            password=password1,
            first_name=real_name,
            nickname=nickname,
            dong=dong,
            ho=ho,
            unit_number=f'{dong}동 {ho}호',
            phone_number=phone,
            email=email,
        )
        # 관리비 고지서 첨부 여부에 따라 인증 상태 설정
        doc = request.FILES.get('verify_document')
        if doc:
            user.profile_image = doc
            user.verified_note = '인증 대기중 [고지서 제출]'
            user.save(update_fields=['profile_image', 'verified_note'])
            messages.success(request, f'가입 신청 완료! {nickname}님 환영합니다 🎉 관리비 고지서를 확인 후 빠르게 승인됩니다.')
        else:
            user.verified_note = '인증 대기중'
            user.save(update_fields=['verified_note'])
            messages.success(request, f'가입 신청 완료! {nickname}님 환영합니다 🎉 관리자가 거주 여부 확인 후 승인됩니다. 다소 시간이 소요될 수 있습니다.')
        return redirect('login')
    return render(request, 'registration/signup.html')

@login_required
def mypage(request):
    user = request.user
    from .models import Group, GroupMember, UserBadge, Survey, SurveyResponse, Rating
    my_posts       = Post.objects.filter(author=user, is_active=True).order_by('-created_at')[:5]
    my_comments    = Comment.objects.filter(author=user, is_active=True).order_by('-created_at')[:5]
    my_activities  = ActivityProof.objects.filter(user=user).order_by('-submitted_at')[:5]
    my_badges      = UserBadge.objects.filter(user=user).select_related('badge').order_by('-earned_at')
    my_groups      = Group.objects.filter(members=user, is_active=True)
    my_surveys     = Survey.objects.filter(creator=user).order_by('-created_at')[:3]
    my_responses   = SurveyResponse.objects.filter(respondent=user).select_related('survey').order_by('-submitted_at')[:3]
    received_ratings = Rating.objects.filter(rated_user=user).order_by('-created_at')[:5]
    total_activities = ActivityProof.objects.filter(user=user, status='approved').count()
    pending_activities = ActivityProof.objects.filter(user=user, status='pending').count()
    user_grade_name = get_user_grade(user)
    try:
        user_grade = MemberGrade.objects.get(name=str(user_grade_name)) if user_grade_name else None
    except:
        user_grade = None
    from .models import Letter, Complaint, Notification
    from django.utils import timezone
    from datetime import timedelta
    unread_letters   = Letter.objects.filter(receiver=user, is_read=False, receiver_deleted=False).count()
    my_complaints    = Complaint.objects.filter(author=user).order_by('-created_at')[:3]
    pending_complaints = Complaint.objects.filter(author=user, status__in=['received','reviewing']).count()
    unread_noti      = Notification.objects.filter(recipient=user, is_read=False).count()
    week_ago         = timezone.now() - timedelta(days=7)
    recent_posts     = Post.objects.filter(author=user, created_at__gte=week_ago).count()

    return render(request, 'mypage.html', {
        'user': user,
        'my_posts': my_posts,
        'my_comments': my_comments,
        'my_activities': my_activities,
        'my_badges': my_badges,
        'my_groups': my_groups,
        'my_surveys': my_surveys,
        'my_responses': my_responses,
        'received_ratings': received_ratings,
        'user_grade': user_grade,
        'total_activities': total_activities,
        'pending_activities': pending_activities,
        'total_points': user.mileage_points,
        'unread_letters': unread_letters,
        'my_complaints': my_complaints,
        'pending_complaints': pending_complaints,
        'unread_noti': unread_noti,
        'recent_posts': recent_posts,
    })


# ============================================================================
# 게시판
# ============================================================================
def board_list(request):
    from .models import Post
    # 기록하기: 나눔/장터(trade), 민원/오류(complaint), FAQ(faq) 제외
    # 기록하기: 건의와FAQ(id=13), 나눔/장터(id=14) 제외
    boards = Board.objects.filter(is_active=True).exclude(id__in=[13, 14]).order_by('order')
    boards_with_posts = []
    for board in boards:
        recent = Post.objects.filter(board=board, is_active=True).order_by('-created_at')[:2]
        boards_with_posts.append({'board': board, 'recent_posts': recent})
    return render(request, 'board_list.html', {'boards_with_posts': boards_with_posts})

def board_detail(request, board_id):
    board = get_object_or_404(Board, pk=board_id, is_active=True)
    if not check_board_permission(request.user, board, 'read'):
        # 비로그인/미승인 → 티저 페이지
        reason = 'login' if not request.user.is_authenticated else 'verify'
        return render(request, 'board_detail_teaser.html', {
            'board': board,
            'reason': reason,
        })
    tag = request.GET.get('tag', '')
    q   = request.GET.get('q', '')
    posts = Post.objects.filter(board=board, is_active=True)
    if tag:
        posts = posts.filter(tag=tag)
    if q:
        posts = posts.filter(title__icontains=q) | posts.filter(content__icontains=q)
    posts = posts.order_by('-is_pinned', '-created_at')
    return render(request, 'board_detail.html', {
        'board':       board,
        'posts':       posts,
        'total_count': posts.count(),
        'tags':        board.get_tags_list(),
        'selected_tag': tag,
        'q':           q,
        'can_write':   check_board_permission(request.user, board, 'write'),
        'can_comment': check_board_permission(request.user, board, 'comment'),
    })

def post_list(request):
    board_id = request.GET.get('board_id')
    selected_board = None
    selected_tag   = request.GET.get('tag', '')
    posts = Post.objects.filter(is_active=True)
    if board_id:
        selected_board = get_object_or_404(Board, pk=board_id, is_active=True)
        posts = posts.filter(board=selected_board)
    if selected_tag:
        posts = posts.filter(tag=selected_tag)
    boards = Board.objects.filter(is_active=True).order_by('order')
    active_boards = boards.exclude(board_type__in=['trade','qna','gallery','faq','complaint']).exclude(name__in=['FAQ','나눔/장터','민원/오류','민원·건의'])
    return render(request, 'core/post_list.html', {
        'posts': posts.order_by('-created_at'),
        'boards': boards,
        'selected_board': selected_board,
        'selected_tag': selected_tag,
    })

def post_detail(request, pk):
    post     = get_object_or_404(Post, pk=pk, is_active=True)
    Post.objects.filter(pk=pk).update(view_count=post.view_count+1)

    # 비로그인 또는 미승인 → 티저 페이지
    if not request.user.is_authenticated:
        return render(request, 'post_detail_teaser.html', {'post': post, 'reason': 'login'})
    if not request.user.is_verified and not request.user.is_staff:
        return render(request, 'post_detail_teaser.html', {'post': post, 'reason': 'verify'})

    comments = post.comments.filter(is_active=True, parent=None)
    user_groups = []
    if request.user.is_authenticated:
        from .models import Group
        user_groups = Group.objects.filter(members=request.user, is_active=True)[:5]
    # 연결된 설문
    linked_surveys = Survey.objects.filter(source_post=post, status__in=['active','closed'])
    # 관련 게시글
    related_posts = post.related_posts.filter(is_active=True)[:5]
    return render(request, 'post_detail.html', {'user_groups': user_groups,
        'post': post,
        'comments': comments,
        'can_comment': check_board_permission(request.user, post.board, 'comment'),
        'can_write':   check_board_permission(request.user, post.board, 'write'),
        'linked_surveys': linked_surveys,
        'related_posts': related_posts,
    })

@login_required
def post_write(request, board_id):
    from .forms import PostForm, TradeForm, EventForm
    board = get_object_or_404(Board, pk=board_id, is_active=True)
    if not check_board_permission(request.user, board, 'write'):
        return HttpResponseForbidden('이 게시판에 글을 쓸 권한이 없습니다.')
    extra_form_class = TradeForm if board.board_type == 'trade' else (EventForm if board.board_type == 'event' else None)
    if request.method == 'POST':
        post_form  = PostForm(request.POST, board=board)
        extra_form = extra_form_class(request.POST) if extra_form_class else None
        if post_form.is_valid() and (extra_form is None or extra_form.is_valid()):
            post = post_form.save(commit=False)
            post.board  = board
            post.author = request.user
            post.save()
            if extra_form:
                extra = extra_form.save(commit=False)
                extra.post = post
                extra.save()
            # 이미지 첨부 처리 (파일 업로드)
            images = request.FILES.getlist('images')
            from .models import PostImage
            for i, image in enumerate(images):
                PostImage.objects.create(post=post, image=image, order=i)

            # base64 이미지를 파일로 변환해서 PostImage로 저장
            import re, base64, uuid
            from django.core.files.base import ContentFile
            post_content = post.content
            b64_imgs = re.findall(r'src="data:image/(\w+);base64,([^"]+)"', post_content)
            for idx, (ext, b64data) in enumerate(b64_imgs[:5]):  # 최대 5개
                try:
                    img_data = base64.b64decode(b64data)
                    from django.core.files.storage import default_storage
                    now = post.created_at
                    save_path = f'posts/{now.year}/{now.month:02d}/{uuid.uuid4().hex[:8]}.{ext}'
                    saved = default_storage.save(save_path, ContentFile(img_data))
                    pi = PostImage(post=post, order=len(images)+idx)
                    pi.image.name = saved
                    pi.save()
                    # 본문의 base64를 저장된 URL로 교체
                    post_content = post_content.replace(
                        f'data:image/{ext};base64,{b64data}',
                        pi.image.url
                    )
                except Exception:
                    pass
            if b64_imgs:
                post.content = post_content
                post.save(update_fields=['content'])

            return redirect('post_detail', pk=post.pk)
    else:
        post_form  = PostForm(board=board)
        extra_form = extra_form_class() if extra_form_class else None
    return render(request, 'post_write.html', {
        'board': board,
        'post_form': post_form,
        'extra_form': extra_form,
        'my_surveys': Survey.objects.filter(creator=request.user, status='active') if request.user.is_authenticated else [],
    })

@login_required
def board_post_create(request):
    from .forms import PostForm
    boards = Board.objects.filter(is_active=True).order_by('order')
    active_boards = boards.exclude(board_type__in=['trade','qna','gallery','faq','complaint']).exclude(name__in=['FAQ','나눔/장터','민원/오류','민원·건의'])
    board_id = request.GET.get('board_id') or request.POST.get('board_id')
    board = get_object_or_404(Board, pk=board_id) if board_id else None
    if request.method == 'POST' and board:
        form = PostForm(request.POST, board=board)
        if form.is_valid():
            post = form.save(commit=False)
            post.board  = board
            post.author = request.user
            # 설문 삽입 처리
            survey_id = request.POST.get('linked_survey_id')
            if survey_id:
                try:
                    from .models import Survey
                    survey = Survey.objects.get(pk=int(survey_id), creator=request.user)
                    post.linked_survey = survey
                    # 설문의 source_post 연결
                    if not survey.source_post:
                        survey.source_post = post
                        survey.save()
                except: pass
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(board=board)
    return render(request, 'post_form.html', {'form': form, 'boards': boards, 'selected_board': board})

@login_required
def post_create(request):
    return board_post_create(request)

@login_required
def post_edit(request, pk):
    from .forms import PostForm
    post = get_object_or_404(Post, pk=pk, is_active=True)
    if post.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden('수정 권한이 없습니다.')
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post, board=post.board)
        if form.is_valid():
            form.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post, board=post.board)
    return render(request, 'post_edit.html', {'board': post.board, 'post': post, 'post_form': form})

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk, is_active=True)
    if post.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden('삭제 권한이 없습니다.')
    if request.method == 'POST':
        post.is_active = False
        post.save()
        return redirect('board_detail', board_id=post.board.id)
    return render(request, 'post_delete_confirm.html', {'post': post})

@login_required
def post_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    like, created = PostLike.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
        Post.objects.filter(pk=post_id).update(like_count=post.like_count-1)
        liked = False
    else:
        Post.objects.filter(pk=post_id).update(like_count=post.like_count+1)
        liked = True
    return JsonResponse({'liked': liked, 'count': Post.objects.get(pk=post_id).like_count})

@login_required
def comment_create(request, post_id):
    if request.method == 'POST':
        post    = get_object_or_404(Post, pk=post_id)
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        if content:
            Comment.objects.create(
                post=post, author=request.user,
                content=content,
                parent_id=parent_id if parent_id else None,
            )
    return redirect('post_detail', pk=post_id)


# ============================================================================
# 활동 인증
# ============================================================================
@login_required
def activity_proof_submit(request):
    from .forms import ActivityProofForm
    if request.method == 'POST':
        form = ActivityProofForm(request.POST, request.FILES)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.user   = request.user
            proof.status = 'pending'
            proof.save()
            messages.success(request, '활동 인증이 제출됐습니다! 관리자 승인 후 포인트가 지급됩니다.')
            return redirect('activity_proof_list')
    else:
        form = ActivityProofForm()
    return render(request, 'activity_proof_submit.html', {'form': form})

@login_required
def activity_proof_list(request):
    proofs = ActivityProof.objects.filter(user=request.user).order_by('-submitted_at')
    return render(request, 'activity_proof_list.html', {'proofs': proofs})

def activity_list(request):
    activities = Activity.objects.filter(is_active=True)
    return render(request, 'core/activity_list.html', {'activities': activities})


# ============================================================================
# API ViewSets
# ============================================================================
class PostViewSet(viewsets.ModelViewSet):
    queryset         = Post.objects.all()
    serializer_class = PostSerializer
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class GroupViewSet(viewsets.ModelViewSet):
    queryset         = Group.objects.all()
    serializer_class = GroupSerializer

class MeetupViewSet(viewsets.ModelViewSet):
    queryset         = Meetup.objects.all()
    serializer_class = MeetupSerializer


# ============================================================================
# 프로필 수정
# ============================================================================
@login_required

@login_required
def profile_edit(request):
    user = request.user
    if request.method == 'POST':
        user.nickname     = request.POST.get('nickname', '')
        user.first_name   = request.POST.get('first_name', '')
        dong = request.POST.get('dong', '').strip()
        ho   = request.POST.get('ho', '').strip()
        user.dong = dong
        user.ho   = ho
        user.unit_number = f"{dong}동 {ho}호".strip() if dong or ho else ''
        user.phone_number = request.POST.get('phone_number', '')
        user.introduction = request.POST.get('introduction', '')
        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES['profile_image']
        user.save()
        messages.success(request, '프로필이 수정됐습니다.')
        return redirect('mypage')
    return render(request, 'profile_edit.html', {'user': user})


# ============================================================================
# 봉사활동 달력
# ============================================================================
def volunteer_calendar(request):
    from .models import Meetup
    meetups = Meetup.objects.filter(
        status__in=['planned', 'recruiting', 'confirmed', 'completed']
    ).exclude(status='cancelled').values('id', 'title', 'scheduled_at', 'location', 'status', 'max_participants')
    
    import json
    from django.utils import timezone
    
    events = []
    for m in meetups:
        events.append({
            'id': m['id'],
            'title': m['title'],
            'start': m['scheduled_at'].isoformat() if m['scheduled_at'] else '',
            'location': m['location'],
            'status': m['status'],
            'url': f'/volunteer/{m["id"]}/',
        })
    
    return render(request, 'volunteer_calendar.html', {
        'events_json': json.dumps(events, ensure_ascii=False),
    })

def volunteer_detail(request, pk):
    from .models import Meetup, MeetupRating
    meetup = get_object_or_404(Meetup, pk=pk)
    if meetup.status == 'cancelled':
        messages.warning(request, '취소된 봉사활동입니다.')
        return redirect('volunteer_calendar')
    is_joined = False
    has_rated = False
    if request.user.is_authenticated:
        is_joined = meetup.participants.filter(pk=request.user.pk).exists()
        has_rated = MeetupRating.objects.filter(meetup=meetup, rater=request.user).exists()
    ratings = MeetupRating.objects.filter(meetup=meetup).select_related('rater').order_by('-created_at')
    return render(request, 'volunteer_detail.html', {
        'meetup': meetup,
        'is_joined': is_joined,
        'has_rated': has_rated,
        'ratings': ratings,
        'participant_count': meetup.participants.count(),
    })

@login_required
def volunteer_join(request, pk):
    from .models import Meetup
    meetup = get_object_or_404(Meetup, pk=pk)
    if request.method == 'POST':
        if meetup.participants.filter(pk=request.user.pk).exists():
            meetup.participants.remove(request.user)
            messages.info(request, '참가 신청이 취소됐습니다.')
        else:
            if meetup.max_participants and meetup.participants.count() >= meetup.max_participants:
                messages.error(request, '참가 인원이 마감됐습니다.')
            else:
                meetup.participants.add(request.user)
                messages.success(request, '참가 신청이 완료됐습니다!')
    return redirect('volunteer_detail', pk=pk)


# ============================================================================
# 검색
# ============================================================================
def search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = Post.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tag__icontains=query)
        ).order_by('-created_at')
    return render(request, 'search.html', {
        'query': query,
        'results': results,
        'count': results.count() if query else 0,
    })




# ============================================================================
# 알림 시스템
# ============================================================================
@login_required
def notification_list(request):
    from .models import Notification
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:50]
    # 읽음 처리
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notification_list.html', {
        'notifications': notifications,
    })

def notification_count(request):
    from .models import Notification
    count = 0
    if request.user.is_authenticated:
        noti = Notification.objects.filter(recipient=request.user, is_read=False).count()
        dm = DirectMessage.objects.filter(receiver=request.user, is_read=False).count()
        count = noti + dm
    return JsonResponse({'count': count})


# ============================================================================
# 알림 시스템
# ============================================================================
@login_required
def notification_list(request):
    from .models import Notification
    notis = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:50]
    Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)
    return render(request, 'notification_list.html', {'notifications': notis})


# ============================================================================
# 관리 문서 게시판
# ============================================================================
def management_docs(request):
    from .models import ManagementDocument
    category = request.GET.get('category', '')
    query = request.GET.get('q', '')
    docs = ManagementDocument.objects.filter(is_active=True)
    if category:
        docs = docs.filter(category=category)
    if query:
        docs = docs.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )
    categories = ManagementDocument.objects.filter(
        is_active=True
    ).values_list('category', flat=True).distinct()
    return render(request, 'management_docs.html', {
        'docs': docs.order_by('category', 'title'),
        'categories': categories,
        'selected_category': category,
        'query': query,
    })

def management_doc_detail(request, pk):
    from .models import ManagementDocument
    doc = get_object_or_404(ManagementDocument, pk=pk, is_active=True)
    ManagementDocument.objects.filter(pk=pk).update(view_count=models.F('view_count') + 1)
    doc.refresh_from_db()
    related = ManagementDocument.objects.filter(
        category=doc.category, is_active=True
    ).exclude(pk=pk).order_by('-created_at')[:5]
    return render(request, 'management_doc_detail.html', {'doc': doc, 'related': related})




# ============================================================
# 관리 문서 게시판 - 업로드/삭제
# ============================================================
@login_required
def management_doc_upload(request):
    from .models import ManagementDocument
    if not (request.user.is_staff or get_user_grade(request.user) >= 4):
        from django.contrib import messages
        messages.error(request, '운영진 이상만 문서를 등록할 수 있습니다.')
        return redirect('management_docs')
    if request.method == 'POST':
        title    = request.POST.get('title', '').strip()
        category = request.POST.get('category', '기타')
        content_text = request.POST.get('content', '').strip()
        file     = request.FILES.get('file')
        if not title:
            from django.contrib import messages
            messages.error(request, '제목을 입력해 주세요.')
            return redirect('management_doc_upload')
        doc = ManagementDocument.objects.create(
            title=title,
            category=category,
            content=content_text,
            author=request.user,
        )
        if file:
            doc.file = file
            doc.save()
        from django.contrib import messages
        messages.success(request, f'"{title}" 문서가 등록되었습니다.')
        return redirect('management_doc_detail', pk=doc.pk)
    categories = ManagementDocument.CATEGORY_CHOICES
    return render(request, 'management_doc_upload.html', {'categories': categories})

@login_required
def management_doc_delete(request, pk):
    from .models import ManagementDocument
    doc = get_object_or_404(ManagementDocument, pk=pk)
    if not (request.user.is_staff or request.user == doc.author):
        from django.contrib import messages
        messages.error(request, '삭제 권한이 없습니다.')
        return redirect('management_doc_detail', pk=pk)
    if request.method == 'POST':
        title = doc.title
        doc.is_active = False
        doc.save()
        from django.contrib import messages
        messages.success(request, f'"{title}" 문서가 삭제되었습니다.')
        return redirect('management_docs')
    return render(request, 'management_doc_delete_confirm.html', {'doc': doc})

# =====================================================
# 채팅 시스템
# =====================================================
from .models import DirectMessage, PublicChat, GroupChat, Group, CustomUser

def public_chat(request):
    from .models import PublicChat, Group
    from django.contrib.auth import get_user_model
    User = get_user_model()
    recent_chats = PublicChat.objects.filter(is_active=True).select_related('author').order_by('-created_at')[:50]
    my_groups = Group.objects.filter(members=request.user, is_active=True)[:10] if request.user.is_authenticated else []
    online_users = User.objects.filter(is_active=True).order_by('-last_login')[:20]
    all_users = User.objects.filter(is_active=True).order_by('nickname')[:50]

    # 비로그인/미승인 → 블러 처리된 채팅 페이지
    is_locked = (not request.user.is_authenticated) or                 (not request.user.is_verified and not request.user.is_staff)
    reason = 'login' if not request.user.is_authenticated else 'verify'

    return render(request, 'chat/public_chat.html', {
        'recent_chats': list(reversed(recent_chats)),
        'my_groups': my_groups,
        'online_users': online_users,
        'all_users': all_users,
        'is_locked': is_locked,
        'reason': reason,
    })

def public_chat_messages(request):
    import json
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)

    if request.method == 'POST':
        msg = request.POST.get('message', '').strip()
        image = request.FILES.get('image')
        if not msg and not image:
            return JsonResponse({'error': '내용 없음'}, status=400)
        chat = PublicChat.objects.create(author=request.user, message=msg)
        if image:
            chat.image = image
            chat.save()
        return JsonResponse({'status': 'ok', 'id': chat.id})

    since_id = int(request.GET.get('since', 0))
    # 고정 메시지
    pinned = PublicChat.objects.filter(is_pinned=True, is_active=True).select_related('author').order_by('-created_at')[:3]
    # 일반 메시지
    msgs = PublicChat.objects.filter(id__gt=since_id, is_active=True).select_related('author').order_by('created_at')[:60]

    def serialize(m):
        return {
            'id': m.id,
            'author': m.author.nickname or m.author.username,
            'unit': m.author.unit_number,
            'message': m.message,
            'image': request.build_absolute_uri(m.image.url) if m.image and m.image.name else None,
            'time': m.created_at.strftime('%H:%M'),
            'is_me': m.author == request.user,
            'is_pinned': m.is_pinned,
            'is_admin': m.author.is_staff,
            'can_pin': request.user.is_staff,
        }

    return JsonResponse({
        'messages': [serialize(m) for m in msgs],
        'pinned': [serialize(m) for m in pinned] if since_id == 0 else [],
    })

def dm_list(request):
    """1:1 채팅 상대 목록 + 온라인 유저 + 전체 유저 검색"""
    if not request.user.is_authenticated:
        return redirect('login')
    from django.db.models import Q, Max
    from django.utils import timezone
    from datetime import timedelta

    # 기존 대화 상대
    partners_sent = DirectMessage.objects.filter(sender=request.user).values_list('receiver', flat=True).distinct()
    partners_recv = DirectMessage.objects.filter(receiver=request.user).values_list('sender', flat=True).distinct()
    partner_ids = set(list(partners_sent) + list(partners_recv))
    partners = CustomUser.objects.filter(id__in=partner_ids).exclude(id=request.user.id)

    # 온라인 유저 (최근 5분 이내 로그인)
    online_threshold = timezone.now() - timedelta(minutes=30)
    online_users = CustomUser.objects.filter(
        is_active=True,
        last_login__gte=online_threshold
    ).exclude(id=request.user.id).order_by('-last_login')[:20]

    # 전체 유저 (검색용)
    q = request.GET.get('q', '').strip()
    all_users = CustomUser.objects.filter(is_active=True).exclude(id=request.user.id)
    if q:
        all_users = all_users.filter(
            Q(nickname__icontains=q) | Q(username__icontains=q) | Q(dong__icontains=q)
        )
    all_users = all_users.order_by('nickname')[:30]

    unread_count = DirectMessage.objects.filter(receiver=request.user, is_read=False).count()
    return render(request, 'chat/dm_list.html', {
        'partners': partners,
        'online_users': online_users,
        'all_users': all_users,
        'unread_count': unread_count,
        'q': q,
    })

def direct_message(request, user_id):
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('login')
    partner = get_object_or_404(CustomUser, pk=user_id)
    DirectMessage.objects.filter(sender=partner, receiver=request.user, is_read=False).update(is_read=True)
    all_users = CustomUser.objects.filter(is_active=True).exclude(id=request.user.id).order_by('username')[:20]
    return render(request, 'chat/direct_message.html', {'partner': partner, 'all_users': all_users})

def dm_messages(request, user_id):
    import json
    from django.http import JsonResponse
    from django.db.models import Q
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)
    partner = get_object_or_404(CustomUser, pk=user_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            msg = data.get('message', '').strip()
        except Exception:
            msg = request.POST.get('message', '').strip()
        image = request.FILES.get('image')
        if not msg and not image:
            return JsonResponse({'error': '내용 없음'}, status=400)
        dm = DirectMessage.objects.create(sender=request.user, receiver=partner, message=msg)
        if image:
            dm.image = image
            dm.save()
        return JsonResponse({'status': 'ok', 'id': dm.id})

    since_id = int(request.GET.get('since', 0))
    msgs = DirectMessage.objects.filter(
        Q(sender=request.user, receiver=partner) | Q(sender=partner, receiver=request.user),
        id__gt=since_id, is_active=True
    ).select_related('sender').order_by('created_at')[:100]
    DirectMessage.objects.filter(sender=partner, receiver=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'messages': [
        {
            'id': m.id,
            'author': m.sender.username,
            'unit': m.sender.unit_number,
            'message': m.message,
            'image': request.build_absolute_uri(m.image.url) if m.image and m.image.name else None,
            'time': m.created_at.strftime('%H:%M'),
            'is_me': m.sender == request.user,
            'is_read': m.is_read,
        } for m in msgs
    ]})


def group_chat_redirect(request):
    """소모임 채팅 목록 페이지"""
    from django.shortcuts import render, redirect
    if not request.user.is_authenticated:
        return redirect('/login/')
    from hello_world.core.models import GroupMember
    memberships = GroupMember.objects.filter(user=request.user).select_related('group').order_by('-joined_at')
    return render(request, 'chat/group_chat_list.html', {'memberships': memberships})

def group_chat(request, group_id):
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('login')
    group = get_object_or_404(Group, pk=group_id)
    from .models import GroupMember
    members = GroupMember.objects.filter(group=group, is_active=True).select_related('user')
    my_groups = Group.objects.filter(members=request.user, is_active=True)[:5]
    return render(request, 'chat/group_chat.html', {'group': group, 'members': members, 'my_groups': my_groups})

def group_chat_messages(request, group_id):
    import json
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)
    group = get_object_or_404(Group, pk=group_id)

    if request.method == 'POST':
        msg = request.POST.get('message', '').strip()
        image = request.FILES.get('image')
        if not msg and not image:
            return JsonResponse({'error': '내용 없음'}, status=400)
        chat = GroupChat.objects.create(group=group, sender=request.user, message=msg)
        if image:
            chat.image = image
            chat.save()
        return JsonResponse({'status': 'ok', 'id': chat.id})

    since_id = int(request.GET.get('since', 0))
    pinned = GroupChat.objects.filter(group=group, is_pinned=True, is_active=True).select_related('sender').order_by('-created_at')[:3]
    msgs = GroupChat.objects.filter(group=group, id__gt=since_id, is_active=True).select_related('sender').order_by('created_at')[:100]

    def serialize(m):
        return {
            'id': m.id,
            'author': m.sender.username,
            'unit': m.sender.unit_number,
            'message': m.message,
            'image': request.build_absolute_uri(m.image.url) if m.image and m.image.name else None,
            'time': m.created_at.strftime('%H:%M'),
            'is_me': m.sender == request.user,
            'is_pinned': m.is_pinned,
            'can_pin': request.user.is_staff,
        }

    return JsonResponse({
        'messages': [serialize(m) for m in msgs],
        'pinned': [serialize(m) for m in pinned] if since_id == 0 else [],
    })


# ============================================================================
# 소모임 (Group)
# ============================================================================
@login_required
def group_list(request):
    from .models import Group, GroupMember
    GROUP_TYPE_LABELS = {
        'hobby': '취미 활동', 'pet': '반려동물', 'sports': '스포츠',
        'volunteer': '자원봉사', 'learning': '학습', 'event': '정기 행사',
    }
    q          = request.GET.get('q', '').strip()
    gtype      = request.GET.get('type', '')
    order      = request.GET.get('order', 'newest')

    from django.db.models import Q, Count
    qs = Group.objects.filter(is_active=True, is_public=True)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if gtype:
        qs = qs.filter(group_type=gtype)
    if order == 'members':
        qs = qs.annotate(mc=Count('members')).order_by('-mc')
    else:
        qs = qs.order_by('-created_at')

    my_groups  = Group.objects.filter(members=request.user, is_active=True) if request.user.is_authenticated else Group.objects.none()
    all_groups = qs.exclude(members=request.user) if request.user.is_authenticated else qs

    return render(request, 'group_list.html', {
        'my_groups':         my_groups,
        'all_groups':        all_groups,
        'q':                 q,
        'gtype':             gtype,
        'order':             order,
        'group_type_labels': GROUP_TYPE_LABELS,
    })


@login_required
@login_required
def group_create(request):
    from .models import Group, GroupMember, GroupLeaderLog
    from django.utils import timezone
    GROUP_TYPE = [
        ('hobby', '취미 활동'), ('pet', '반려동물'), ('sports', '스포츠'),
        ('volunteer', '자원봉사'), ('learning', '학습'), ('event', '정기 행사'),
    ]
    if request.method == 'POST':
        name             = request.POST.get('name', '').strip()
        description      = request.POST.get('description', '').strip()
        group_type       = request.POST.get('group_type', 'hobby')
        location         = request.POST.get('location', '').strip()
        regular_schedule = request.POST.get('regular_schedule', '').strip()
        member_limit     = request.POST.get('member_limit') or None
        is_public        = request.POST.get('is_public') == 'on'
        join_type        = request.POST.get('join_type', 'open')
        is_limited       = request.POST.get('is_limited') == 'on'
        expires_at_str   = request.POST.get('expires_at', '').strip()

        if not name:
            messages.error(request, '소모임 이름을 입력해주세요.')
            return render(request, 'group_form.html', {'group_types': GROUP_TYPE})

        limit_int = int(member_limit) if member_limit else None
        # 10인 이상이면 관리자 승인 필요
        needs_approval = limit_int and limit_int >= 10
        status = 'pending' if needs_approval else 'active'

        expires_at = None
        if is_limited and expires_at_str:
            from django.utils.dateparse import parse_datetime
            expires_at = parse_datetime(expires_at_str + ':00') if len(expires_at_str) == 16 else None

        group = Group.objects.create(
            name=name, description=description, group_type=group_type,
            creator=request.user, location=location,
            regular_schedule=regular_schedule,
            member_limit=limit_int,
            is_public=is_public,
            join_type=join_type,
            is_limited=is_limited,
            expires_at=expires_at,
            status=status,
        )
        GroupMember.objects.create(
            group=group, user=request.user, role='leader',
            join_status='approved', approved_at=timezone.now()
        )
        GroupLeaderLog.objects.create(
            group=group, actor=request.user, action='create',
            detail=f'소모임 생성 (정원:{limit_int}, 가입:{join_type})'
        )
        if needs_approval:
            messages.warning(request, f'"{name}" 소모임이 생성됐어요. 정원 10인 이상은 관리자 승인 후 활성화됩니다.')
        else:
            messages.success(request, f'소모임 "{name}"이 만들어졌어요! 이웃을 초대해보세요.')
        return redirect('group_detail', pk=group.pk)
    return render(request, 'group_form.html', {'group_types': GROUP_TYPE})


def group_detail(request, pk):
    import json
    from .models import Group, GroupMember, GroupPost, GroupLeaderLog, CalendarEvent, Survey
    from django.db.models import Q
    group = get_object_or_404(Group, pk=pk)
    is_member = False
    my_role = None
    membership = None
    if request.user.is_authenticated:
        membership = GroupMember.objects.filter(group=group, user=request.user, is_active=True).first()
        is_member = bool(membership)
        my_role = membership.role if membership else None

    # 가입 대기중인지
    pending = False
    invited = False
    if request.user.is_authenticated and not is_member:
        pending = GroupMember.objects.filter(
            group=group, user=request.user, join_status='pending'
        ).exists()
        invited = GroupMember.objects.filter(
            group=group, user=request.user, join_status='invited'
        ).exists()

    members = GroupMember.objects.filter(
        group=group, is_active=True, join_status='approved'
    ).select_related('user').order_by('joined_at')

    pending_members = []
    leader_logs = []
    if my_role in ('leader', 'moderator'):
        pending_members = GroupMember.objects.filter(
            group=group, join_status='pending'
        ).select_related('user')
        leader_logs = GroupLeaderLog.objects.filter(group=group).select_related('actor','target')[:20]

    recent_posts = GroupPost.objects.filter(group=group).order_by('-created_at')[:5]
    group_events = CalendarEvent.objects.filter(group=group, visibility__in=['group','group_pending','public']).order_by('start_time')[:5]
    from .models import Poll
    group_polls = Poll.objects.filter(group=group, is_active=True).order_by('-created_at')

    return render(request, 'group_detail.html', {
        'group':           group,
        'is_member':       is_member,
        'my_role':         my_role,
        'pending':         pending,
        'membership':      membership,
        'members':         members,
        'pending_members': pending_members,
        'leader_logs':     leader_logs,
        'recent_posts':    recent_posts,
        'group_events':    group_events,
        'member_count':    members.count(),
        'is_leader':       my_role == 'leader',
        'is_mod':          my_role in ('leader', 'moderator'),
        'invited':         invited,
        'group_polls':     group_polls,
        'group_events_json': json.dumps([{
            'id':          e.id,
            'title':       e.title,
            'start':       e.start_time.isoformat(),
            'end':         e.end_time.isoformat() if e.end_time else None,
            'location':    e.location,
            'description': e.description,
            'cal_id':      e.id,
            'rrule':       e.rrule if e.rrule else None,
            'duration':    (
                f'{int((e.end_time - e.start_time).total_seconds() // 3600):02d}:{int(((e.end_time - e.start_time).total_seconds() % 3600) // 60):02d}'
                if e.end_time else None
            ),
        } for e in group_events], ensure_ascii=False),
    })


@login_required
def group_join(request, pk):
    from .models import Group, GroupMember, GroupLeaderLog
    from django.utils import timezone
    group = get_object_or_404(Group, pk=pk)
    if request.method != 'POST':
        return redirect('group_detail', pk=pk)

    existing = GroupMember.objects.filter(group=group, user=request.user).first()

    # 탈퇴 처리
    if existing and existing.is_active and existing.join_status == 'approved':
        if existing.role == 'leader':
            messages.error(request, '방장은 탈퇴할 수 없어요. 먼저 방장을 위임하세요.')
            return redirect('group_detail', pk=pk)
        existing.is_active = False
        existing.save()
        messages.info(request, f'"{group.name}" 소모임에서 나왔어요.')
        return redirect('group_detail', pk=pk)

    # 정원 확인
    current_count = GroupMember.objects.filter(group=group, is_active=True, join_status='approved').count()
    if group.member_limit and current_count >= group.member_limit:
        messages.error(request, '참여 인원이 가득 찼어요.')
        return redirect('group_detail', pk=pk)

    # 가입 방식별 처리
    if group.join_type == 'open':
        if existing:
            existing.is_active = True
            existing.join_status = 'approved'
            existing.approved_at = timezone.now()
            existing.save()
        else:
            GroupMember.objects.create(
                group=group, user=request.user, role='member',
                join_status='approved', approved_at=timezone.now()
            )
        messages.success(request, f'"{group.name}" 소모임에 참여했어요!')

    elif group.join_type == 'approve':
        if existing and existing.join_status == 'pending':
            messages.info(request, '이미 가입 신청 중이에요. 방장 승인을 기다려주세요.')
        else:
            GroupMember.objects.update_or_create(
                group=group, user=request.user,
                defaults={'join_status': 'pending', 'is_active': True, 'role': 'member'}
            )
            # 방장에게 알림
            leader_member = GroupMember.objects.filter(group=group, role='leader', is_active=True).first()
            if leader_member:
                from .models import Notification
                Notification.objects.create(
                    recipient=leader_member.user,
                    title=f'[{group.name}] 가입 신청',
                    message=f'{request.user.nickname or request.user.username}님이 가입을 신청했어요.',
                    notification_type='community',
                )
            messages.success(request, '가입 신청이 완료됐어요. 방장 승인을 기다려주세요.')

    elif group.join_type == 'invite':
        messages.error(request, '초대제 소모임은 초대를 통해서만 가입할 수 있어요.')

    return redirect('group_detail', pk=pk)


@login_required
def group_member_action(request, pk):
    """방장/운영진의 회원 관리 액션"""
    from .models import Group, GroupMember, GroupLeaderLog
    from django.utils import timezone
    group = get_object_or_404(Group, pk=pk)
    my_membership = GroupMember.objects.filter(group=group, user=request.user, is_active=True).first()
    if not my_membership or my_membership.role not in ('leader', 'moderator'):
        messages.error(request, '권한이 없어요.')
        return redirect('group_detail', pk=pk)

    action      = request.POST.get('action')
    target_id   = request.POST.get('user_id')
    reason      = request.POST.get('reason', '')
    target_user = get_object_or_404(CustomUser, pk=target_id)
    target_mem  = GroupMember.objects.filter(group=group, user=target_user).first()

    if action == 'approve' and target_mem:
        target_mem.join_status = 'approved'
        target_mem.approved_at = timezone.now()
        target_mem.approved_by = request.user
        target_mem.save()
        GroupLeaderLog.objects.create(group=group, actor=request.user, target=target_user, action='approve')
        messages.success(request, f'{target_user.nickname or target_user.username}님의 가입을 승인했어요.')

    elif action == 'reject' and target_mem:
        target_mem.join_status = 'rejected'
        target_mem.is_active = False
        target_mem.save()
        GroupLeaderLog.objects.create(group=group, actor=request.user, target=target_user, action='reject', detail=reason)
        messages.info(request, f'가입 신청을 거절했어요.')

    elif action == 'ban' and target_mem:
        if target_mem.role == 'leader':
            messages.error(request, '방장은 강제퇴장할 수 없어요.')
        else:
            target_mem.is_active = False
            target_mem.join_status = 'banned'
            target_mem.ban_reason = reason
            target_mem.save()
            GroupLeaderLog.objects.create(group=group, actor=request.user, target=target_user, action='ban', detail=reason)
            messages.success(request, f'{target_user.nickname or target_user.username}님을 퇴장시켰어요.')

    elif action == 'delegate' and my_membership.role == 'leader':
        my_membership.role = 'member'
        my_membership.save()
        if target_mem:
            target_mem.role = 'leader'
            target_mem.save()
        group.creator = target_user
        group.save()
        GroupLeaderLog.objects.create(group=group, actor=request.user, target=target_user, action='delegate')
        messages.success(request, f'{target_user.nickname or target_user.username}님에게 방장을 위임했어요.')

    return redirect('group_detail', pk=pk)


@login_required
def group_invite_respond(request, pk):
    """소모임 초대 수락/거절"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from .models import Group, GroupMember, Notification
    from django.utils import timezone
    group = get_object_or_404(Group, pk=pk)
    membership = GroupMember.objects.filter(group=group, user=request.user, join_status='invited').first()
    if not membership:
        messages.error(request, '초대 정보를 찾을 수 없어요.')
        return redirect('group_list')
    action = request.POST.get('action')
    if action == 'accept':
        membership.join_status = 'approved'
        membership.is_active = True
        membership.approved_at = timezone.now()
        membership.save()
        messages.success(request, f'✅ "{group.name}" 소모임에 참여했어요!')
        return redirect('group_detail', pk=pk)
    elif action == 'decline':
        membership.join_status = 'rejected'
        membership.is_active = False
        membership.save()
        messages.info(request, f'초대를 거절했어요.')
        return redirect('group_list')
    return redirect('group_list')

@login_required
def group_leave(request, pk):
    """소모임 탈퇴"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from .models import Group, GroupMember, GroupLeaderLog
    group = get_object_or_404(Group, pk=pk)
    membership = GroupMember.objects.filter(group=group, user=request.user, is_active=True).first()
    if not membership:
        messages.error(request, '소모임 멤버가 아니에요.')
        return redirect('group_list')
    if membership.role == 'leader':
        messages.error(request, '방장은 탈퇴할 수 없어요. 방장을 위임한 후 탈퇴해주세요.')
        return redirect('group_detail', pk=pk)
    if request.method == 'POST':
        membership.is_active = False
        membership.join_status = 'rejected'
        membership.save()
        GroupLeaderLog.objects.create(
            group=group, actor=request.user, target=request.user,
            action='edit', detail=f'{request.user.nickname or request.user.username}님이 소모임 탈퇴'
        )
        messages.success(request, f'"{group.name}" 소모임에서 탈퇴했어요.')
        return redirect('group_list')
    return redirect('group_detail', pk=pk)

@login_required
def group_dissolve(request, pk):
    """소모임 해체 신청 / 투표"""
    from .models import Group, GroupMember, GroupLeaderLog, GroupDissolveVote
    from django.utils import timezone
    from datetime import timedelta
    group = get_object_or_404(Group, pk=pk)
    my_membership = GroupMember.objects.filter(group=group, user=request.user, role='leader', is_active=True).first()

    if not my_membership:
        messages.error(request, '방장만 해체를 신청할 수 있어요.')
        return redirect('group_detail', pk=pk)

    member_count = GroupMember.objects.filter(group=group, is_active=True, join_status='approved').count()

    if member_count >= 5:
        # 5인 이상 → 해체 투표
        vote, created = GroupDissolveVote.objects.get_or_create(
            group=group,
            defaults={
                'started_by': request.user,
                'ends_at': timezone.now() + timedelta(days=7),
            }
        )
        group.status = 'dissolving'
        group.dissolve_vote_at = timezone.now()
        group.save()
        GroupLeaderLog.objects.create(group=group, actor=request.user, action='dissolve', detail='해체 투표 시작')
        messages.warning(request, '해체 투표가 시작됐어요. 7일 내 과반의 반대가 없으면 해체됩니다.')
    else:
        # 5인 미만 → 즉시 해체
        group.status = 'dissolved'
        group.is_active = False
        group.save()
        GroupLeaderLog.objects.create(group=group, actor=request.user, action='dissolve', detail='즉시 해체')
        messages.info(request, f'"{group.name}" 소모임이 해체됐어요.')
        return redirect('group_list')

    return redirect('group_detail', pk=pk)


# ============================================================================
# 채팅 고정 / 삭제 API
# ============================================================================
from django.views.decorators.http import require_POST

@require_POST
@login_required
def pin_public_chat(request, msg_id):
    from django.http import JsonResponse
    if not request.user.is_staff:
        return JsonResponse({'error': '권한 없음'}, status=403)
    chat = get_object_or_404(PublicChat, pk=msg_id)
    chat.is_pinned = not chat.is_pinned
    chat.save()
    return JsonResponse({'is_pinned': chat.is_pinned})

@require_POST
@login_required
def delete_public_chat(request, msg_id):
    from django.http import JsonResponse
    chat = get_object_or_404(PublicChat, pk=msg_id)
    if chat.author != request.user and not request.user.is_staff:
        return JsonResponse({'error': '권한 없음'}, status=403)
    chat.is_active = False
    chat.save()
    return JsonResponse({'status': 'ok'})

@require_POST
@login_required
def pin_group_chat(request, msg_id):
    from django.http import JsonResponse
    if not request.user.is_staff:
        return JsonResponse({'error': '권한 없음'}, status=403)
    chat = get_object_or_404(GroupChat, pk=msg_id)
    chat.is_pinned = not chat.is_pinned
    chat.save()
    return JsonResponse({'is_pinned': chat.is_pinned})



# ============================================================================
# 설문조사 (업그레이드)
# ============================================================================
from .models import Survey, SurveyQuestion, SurveyResponse
import json as _json

def survey_list(request):
    active_surveys = Survey.objects.filter(status='active').select_related('creator').order_by('-created_at')
    closed_surveys = Survey.objects.filter(status='closed').select_related('creator').order_by('-created_at')
    my_surveys = Survey.objects.filter(creator=request.user).select_related('creator').order_by('-created_at') if request.user.is_authenticated else []
    # 내가 응답한 설문 ID
    responded_ids = set()
    if request.user.is_authenticated:
        responded_ids = set(SurveyResponse.objects.filter(
            respondent=request.user
        ).values_list('survey_id', flat=True))
    return render(request, 'survey/survey_list.html', {
        'active_surveys': active_surveys,
        'closed_surveys': closed_surveys,
        'my_surveys': my_surveys,
        'responded_ids': responded_ids,
    })

@login_required
def survey_create(request):
    if request.method == 'POST':
        title = request.POST.get('title','').strip()
        description = request.POST.get('description','').strip()
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        allow_multiple = request.POST.get('allow_multiple') == 'on'
        show_result = request.POST.get('show_result', 'always')
        ends_at_str = request.POST.get('ends_at','').strip()

        if not title:
            messages.error(request, '설문 제목을 입력해주세요.')
            return render(request, 'survey/survey_form.html')

        from django.utils import timezone
        import datetime
        ends_at = None
        if ends_at_str:
            try:
                ends_at = timezone.make_aware(datetime.datetime.fromisoformat(ends_at_str))
            except: pass

        # from_post 처리
        from_post_id = request.POST.get('from_post') or request.GET.get('from_post')
        source_post = None
        if from_post_id:
            try:
                source_post = Post.objects.get(pk=int(from_post_id), is_active=True)
            except: pass

        survey = Survey.objects.create(
            title=title, description=description,
            creator=request.user, is_anonymous=is_anonymous,
            allow_multiple=allow_multiple, ends_at=ends_at,
            source_post=source_post,
        )

        # 질문 파싱 (JSON으로 전달)
        questions_json = request.POST.get('questions_data', '[]')
        try:
            questions_data = _json.loads(questions_json)
        except:
            questions_data = []

        for i, q in enumerate(questions_data):
            if not q.get('text','').strip() and q.get('type') != 'section':
                continue
            SurveyQuestion.objects.create(
                survey=survey,
                text=q.get('text','').strip(),
                description=q.get('description','').strip(),
                question_type=q.get('type','single'),
                options=q.get('options',[]),
                rows=q.get('rows',[]),
                scale_min=int(q.get('scale_min',1)),
                scale_max=int(q.get('scale_max',10)),
                scale_min_label=q.get('scale_min_label',''),
                scale_max_label=q.get('scale_max_label',''),
                is_required=q.get('required',True),
                order=i,
            )

        # 원본 게시글에 자동 댓글 등록
        if source_post:
            from django.contrib.auth import get_user_model
            survey_url = f'/surveys/{survey.pk}/'
            Comment.objects.create(
                post=source_post,
                author=request.user,
                content=f'📊 이 게시글과 연관된 설문이 만들어졌어요!\n제목: {title}\n👉 설문 참여하기: {survey_url}',
            )
            messages.success(request, f'설문이 만들어지고 게시글에 안내 댓글이 등록됐어요!')
        else:
            messages.success(request, f'설문 "{title}"이 만들어졌어요!')
        return redirect('survey_detail', pk=survey.pk)

    return render(request, 'survey/survey_form.html')

def survey_detail(request, pk):
    survey = get_object_or_404(Survey, pk=pk)
    questions = survey.questions.exclude(question_type='section').all() if False else survey.questions.all()
    already_responded = False
    if request.user.is_authenticated and not survey.allow_multiple:
        already_responded = SurveyResponse.objects.filter(
            survey=survey, respondent=request.user
        ).exists()
    return render(request, 'survey/survey_detail.html', {
        'survey': survey,
        'questions': questions,
        'already_responded': already_responded,
        'total': survey.total_responses,
    })

@login_required
def survey_respond(request, pk):
    from django.http import JsonResponse
    survey = get_object_or_404(Survey, pk=pk)
    if not survey.is_active:
        messages.error(request, '마감된 설문입니다.')
        return redirect('survey_detail', pk=pk)
    if not survey.allow_multiple:
        if SurveyResponse.objects.filter(survey=survey, respondent=request.user).exists():
            messages.warning(request, '이미 응답하셨습니다.')
            return redirect('survey_result', pk=pk)

    if request.method == 'POST':
        answers = {}
        for q in survey.questions.all():
            if q.question_type == 'section': continue
            key = f'q_{q.id}'
            if q.question_type == 'multiple':
                answers[str(q.id)] = request.POST.getlist(key)
            elif q.question_type == 'matrix':
                matrix_ans = {}
                for row in q.rows:
                    row_key = f'q_{q.id}_row_{row}'
                    matrix_ans[row] = request.POST.get(row_key, '')
                answers[str(q.id)] = matrix_ans
            elif q.question_type == 'rank':
                answers[str(q.id)] = request.POST.get(key, '').split(',')
            else:
                answers[str(q.id)] = request.POST.get(key, '')

        SurveyResponse.objects.create(
            survey=survey,
            respondent=request.user,
            answers=answers,
        )
        messages.success(request, '응답이 제출됐어요! 고마워요 😊')
        return redirect('survey_result', pk=pk)

    return redirect('survey_detail', pk=pk)

def survey_result(request, pk):
    survey = get_object_or_404(Survey, pk=pk)
    questions = survey.questions.exclude(question_type='section')
    responses = SurveyResponse.objects.filter(survey=survey).order_by('-submitted_at')

    stats = {}
    for q in questions:
        s = {
            'id': q.id,
            'question': q.text,
            'type': q.question_type,
            'options': q.options,
            'rows': q.rows,
            'scale_min': q.scale_min,
            'scale_max': q.scale_max,
            'scale_min_label': q.scale_min_label,
            'scale_max_label': q.scale_max_label,
            'counts': {},
            'texts': [],
            'dates': [],
            'matrix': {},
            'rank_scores': {},
            'total': 0,
            'avg': 0,
        }
        total = 0
        val_sum = 0

        for resp in responses:
            ans = resp.answers.get(str(q.id))
            if not ans and ans != 0: continue
            total += 1

            if q.question_type in ('single',):
                s['counts'][ans] = s['counts'].get(ans, 0) + 1
            elif q.question_type == 'multiple':
                for a in (ans if isinstance(ans, list) else [ans]):
                    if a: s['counts'][a] = s['counts'].get(a, 0) + 1
            elif q.question_type in ('text',):
                if ans: s['texts'].append(ans)
            elif q.question_type in ('rating', 'scale'):
                try:
                    v = float(ans)
                    val_sum += v
                    k = str(int(v)) if v == int(v) else str(v)
                    s['counts'][k] = s['counts'].get(k, 0) + 1
                except: pass
            elif q.question_type in ('date', 'daterange'):
                if ans: s['dates'].append(ans if isinstance(ans, str) else str(ans))
                s['counts'][str(ans)[:10] if ans else ''] = s['counts'].get(str(ans)[:10] if ans else '', 0) + 1
            elif q.question_type == 'matrix':
                if isinstance(ans, dict):
                    for row, val in ans.items():
                        if row not in s['matrix']: s['matrix'][row] = {}
                        if val: s['matrix'][row][val] = s['matrix'][row].get(val, 0) + 1
            elif q.question_type == 'rank':
                if isinstance(ans, list):
                    for idx, item in enumerate(ans):
                        if item:
                            score = len(ans) - idx
                            s['rank_scores'][item] = s['rank_scores'].get(item, 0) + score

        s['total'] = total
        if q.question_type in ('rating','scale') and total > 0:
            s['avg'] = round(val_sum / total, 1)
        if q.question_type == 'rank' and s['rank_scores']:
            s['rank_scores'] = dict(sorted(s['rank_scores'].items(), key=lambda x: -x[1]))
        stats[q.id] = s

    # 차트 데이터
    chart_data = {}
    for qid, s in stats.items():
        if s['counts']:
            chart_data[str(qid)] = {
                'labels': list(s['counts'].keys()),
                'data': list(s['counts'].values()),
                'type': s['type'],
            }
        elif s['rank_scores']:
            chart_data[str(qid)] = {
                'labels': list(s['rank_scores'].keys()),
                'data': list(s['rank_scores'].values()),
                'type': 'rank',
            }

    # 응답자 목록 (관리자/작성자만)
    show_respondents = (request.user == survey.creator or request.user.is_staff)
    respondents = responses.select_related('respondent') if show_respondents else []

    return render(request, 'survey/survey_result.html', {
        'survey': survey,
        'stats': stats,
        'chart_data': _json.dumps(chart_data, ensure_ascii=False),
        'total_responses': responses.count(),
        'show_respondents': show_respondents,
        'respondents': respondents,
        'questions': questions,
    })

@login_required
def survey_close(request, pk):
    survey = get_object_or_404(Survey, pk=pk, creator=request.user)
    if request.method == 'POST':
        survey.status = 'closed'
        survey.save()
        messages.success(request, '설문이 마감됐습니다.')
    return redirect('survey_result', pk=pk)

@login_required
def survey_delete(request, pk):
    survey = get_object_or_404(Survey, pk=pk, creator=request.user)
    if request.method == 'POST':
        survey.delete()
        messages.success(request, '설문이 삭제됐습니다.')
        return redirect('survey_list')
    return redirect('survey_detail', pk=pk)

@login_required
def survey_export(request, pk):
    """CSV 내보내기"""
    import csv
    from django.http import HttpResponse
    survey = get_object_or_404(Survey, pk=pk)
    if survey.creator != request.user and not request.user.is_staff:
        messages.error(request, '권한이 없습니다.')
        return redirect('survey_result', pk=pk)

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="survey_{pk}.csv"'
    writer = csv.writer(response)

    questions = survey.questions.exclude(question_type='section')
    header = ['응답번호', '응답일시', '응답자'] + [q.text for q in questions]
    writer.writerow(header)

    for i, resp in enumerate(SurveyResponse.objects.filter(survey=survey).select_related('respondent'), 1):
        row = [i, resp.submitted_at.strftime('%Y-%m-%d %H:%M'), resp.respondent.username if resp.respondent else '익명']
        for q in questions:
            ans = resp.answers.get(str(q.id), '')
            if isinstance(ans, list): ans = ', '.join(ans)
            elif isinstance(ans, dict): ans = ' / '.join(f"{k}:{v}" for k,v in ans.items())
            row.append(ans)
        writer.writerow(row)

    return response


# ============================================================================
# 이웃 온기 점수 (Rating)
# ============================================================================
from .models import Rating

@login_required
def rate_user(request, user_id):
    from django.http import JsonResponse
    rated_user = get_object_or_404(CustomUser, pk=user_id)
    if rated_user == request.user:
        return JsonResponse({'error': '본인은 평가할 수 없어요.'}, status=400)
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        score = int(data.get('score', 5))
        comment = data.get('comment', '').strip()
        category = data.get('category', 'general')
        score = max(1, min(5, score))
        rating, created = Rating.objects.update_or_create(
            rater=request.user, rated_user=rated_user,
            defaults={'score': score, 'comment': comment, 'category': category}
        )
        # 온기 점수 재계산 (시그널로 자동 처리)
        from hello_world.core.signals import recalculate_manners_score
        recalculate_manners_score(rated_user)
        # 평가 알림
        if created:
            from .models import Notification
            Notification.objects.create(
                recipient=rated_user,
                title='따뜻한 이웃 온기를 받았어요 ❤️',
                message=f'{request.user.username}님이 온기 점수를 보내줬어요!',
                notification_type='community',
                persona='따뜻한 이웃',
            )
        rated_user.refresh_from_db()
        return JsonResponse({
            'status': 'ok',
            'created': created,
            'new_score': round(rated_user.manners_score, 1),
        })
    # GET: 현재 내 평가 조회
    my_rating = Rating.objects.filter(rater=request.user, rated_user=rated_user).first()
    return JsonResponse({
        'my_score': my_rating.score if my_rating else None,
        'my_comment': my_rating.comment if my_rating else '',
        'total_ratings': Rating.objects.filter(rated_user=rated_user).count(),
        'manners_score': round(rated_user.manners_score, 1),
    })

def user_profile(request, user_id):
    """다른 입주민 프로필 + 온기 평가"""
    from .models import UserFollow
    profile_user = get_object_or_404(CustomUser, pk=user_id)
    ratings = Rating.objects.filter(rated_user=profile_user).order_by('-created_at')[:10]
    my_rating = None
    is_following = False
    is_friend = False
    if request.user.is_authenticated and request.user != profile_user:
        my_rating = Rating.objects.filter(rater=request.user, rated_user=profile_user).first()
        is_following = UserFollow.objects.filter(follower=request.user, following=profile_user).exists()
        is_friend = UserFollow.is_friend(request.user, profile_user)
    total_activities = ActivityProof.objects.filter(user=profile_user, status='approved').count()
    user_badges = profile_user.user_badges.filter(is_displayed=True).select_related('badge')[:6]
    return render(request, 'profile.html', {
        'profile_user':    profile_user,
        'ratings':         ratings,
        'my_rating':       my_rating,
        'total_activities': total_activities,
        'user_badges':     user_badges,
        'can_rate':        request.user.is_authenticated and request.user != profile_user,
        'is_following':    is_following,
        'is_friend':       is_friend,
    })


# ============================================================================
# 관련 게시글 연결
# ============================================================================
@login_required
def link_related_post(request, pk):
    from django.http import JsonResponse
    post = get_object_or_404(Post, pk=pk, is_active=True)
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        target_id = data.get('target_id')
        action = data.get('action', 'add')
        try:
            target = Post.objects.get(pk=int(target_id), is_active=True)
            if action == 'add':
                post.related_posts.add(target)
                return JsonResponse({'status': 'ok', 'msg': f'"{target.title}"와 연결됐어요!'})
            else:
                post.related_posts.remove(target)
                return JsonResponse({'status': 'ok', 'msg': '연결이 해제됐어요.'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    # GET: 관련 게시글 검색
    q = request.GET.get('q', '').strip()
    if q:
        results = Post.objects.filter(
            title__icontains=q, is_active=True
        ).exclude(pk=pk).exclude(related_posts=post)[:10]
        return JsonResponse({'results': [
            {'id': p.id, 'title': p.title, 'board': p.board.name, 'date': p.created_at.strftime('%m.%d')}
            for p in results
        ]})
    return JsonResponse({'results': []})


# ============================================================================
# 설문 결과 → 게시글 자동 발행
# ============================================================================
@login_required
def survey_publish_post(request, pk):
    survey = get_object_or_404(Survey, pk=pk, creator=request.user)
    if request.method == 'POST':
        # 결과 요약 자동 생성
        questions = survey.questions.exclude(question_type='section')
        responses = SurveyResponse.objects.filter(survey=survey).exclude(answers={})
        
        summary_lines = [f'📊 **{survey.title}** 설문 결과 요약\n']
        summary_lines.append(f'총 {responses.count()}명이 참여했습니다.\n')
        
        for q in questions[:5]:  # 최대 5개 질문 요약
            counts = {}
            for resp in responses:
                ans = resp.answers.get(str(q.id), '')
                if not ans: continue
                if isinstance(ans, list):
                    for a in ans:
                        if a: counts[a] = counts.get(a, 0) + 1
                else:
                    counts[str(ans)] = counts.get(str(ans), 0) + 1
            
            if counts:
                total = sum(counts.values())
                summary_lines.append(f'\n**{q.text}**')
                top = sorted(counts.items(), key=lambda x: -x[1])[:3]
                for opt, cnt in top:
                    pct = round(cnt/total*100) if total else 0
                    summary_lines.append(f'- {opt}: {cnt}명 ({pct}%)')
        
        summary_lines.append(f'\n👉 전체 결과 보기: /surveys/{survey.pk}/result/')
        content = '\n'.join(summary_lines)
        
        # 공지 게시판에 자동 발행
        board_id = request.POST.get('board_id')
        try:
            board = Board.objects.get(pk=int(board_id))
        except:
            board = Board.objects.filter(is_active=True).first()
        
        if board:
            post = Post.objects.create(
                board=board,
                author=request.user,
                title=f'[설문결과] {survey.title}',
                content=content,
                tag='설문결과',
                linked_survey=survey,
            )
            survey.source_post = survey.source_post or post
            survey.save()
            messages.success(request, f'설문 결과가 게시글로 발행됐어요!')
            return redirect('post_detail', pk=post.pk)
    
    # GET: 게시판 선택 폼
    boards = Board.objects.filter(is_active=True)
    return render(request, 'survey/survey_publish.html', {
        'survey': survey,
        'boards': boards,
    })


# ============================================================================
# 소모임 게시판
# ============================================================================
def group_post_list(request, pk):
    from .models import Group, GroupMember, GroupPost
    group = get_object_or_404(Group, pk=pk)
    is_member = GroupMember.objects.filter(group=group, user=request.user, is_active=True).exists() if request.user.is_authenticated else False
    posts = GroupPost.objects.filter(group=group).select_related('author').order_by('-created_at')
    return render(request, 'groups/group_post_list.html', {
        'group': group, 'posts': posts, 'is_member': is_member,
    })

@login_required
def group_post_create(request, pk):
    from .models import Group, GroupMember, GroupPost
    group = get_object_or_404(Group, pk=pk)
    if not GroupMember.objects.filter(group=group, user=request.user, is_active=True).exists():
        messages.error(request, '소모임 멤버만 글을 쓸 수 있어요.')
        return redirect('group_detail', pk=pk)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        if not title or not content:
            messages.error(request, '제목과 내용을 입력해주세요.')
            return render(request, 'groups/group_post_form.html', {'group': group})
        post = GroupPost.objects.create(
            group=group, author=request.user,
            title=title, content=content,
        )
        if request.FILES.get('image'):
            post.image = request.FILES['image']
            post.save()
        messages.success(request, '게시글이 등록됐어요!')
        return redirect('group_post_detail', pk=pk, post_pk=post.pk)
    return render(request, 'groups/group_post_form.html', {'group': group})

def group_post_detail(request, pk, post_pk):
    from .models import Group, GroupMember, GroupPost, GroupComment
    group = get_object_or_404(Group, pk=pk)
    post = get_object_or_404(GroupPost, pk=post_pk, group=group)
    is_member = GroupMember.objects.filter(group=group, user=request.user, is_active=True).exists() if request.user.is_authenticated else False
    comments = post.comments.select_related('author').order_by('created_at')
    if request.method == 'POST' and request.user.is_authenticated:
        content = request.POST.get('content', '').strip()
        if content:
            GroupComment.objects.create(post=post, author=request.user, content=content)
            post.comment_count = post.comments.count()
            post.save()
            messages.success(request, '댓글이 등록됐어요!')
        return redirect('group_post_detail', pk=pk, post_pk=post_pk)
    return render(request, 'groups/group_post_detail.html', {
        'group': group, 'post': post,
        'comments': comments, 'is_member': is_member,
    })

@login_required
def group_post_delete(request, pk, post_pk):
    from .models import GroupPost
    post = get_object_or_404(GroupPost, pk=post_pk, author=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, '게시글이 삭제됐어요.')
        return redirect('group_post_list', pk=pk)
    return redirect('group_post_detail', pk=pk, post_pk=post_pk)


# ============================================================================
# 채팅 미니 투표
# ============================================================================
from .models import ChatPoll

def chat_poll_create(request):
    """POST /chat/poll/create/ - /투표 명령어 처리"""
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청'}, status=400)

    import json
    data = json.loads(request.body)
    question = data.get('question', '').strip()
    options = [o.strip() for o in data.get('options', []) if o.strip()]
    chat_type = data.get('chat_type', 'public')
    group_id = data.get('group_id')

    if not question or len(options) < 2:
        return JsonResponse({'error': '질문과 선택지 2개 이상을 입력해주세요'}, status=400)

    group = None
    if group_id:
        from .models import Group
        try:
            group = Group.objects.get(pk=int(group_id))
        except: pass

    poll = ChatPoll.objects.create(
        chat_type=chat_type,
        group=group,
        creator=request.user,
        question=question,
        options=options,
        votes={opt: [] for opt in options},
    )

    # 채팅방에 투표 생성 알림 메시지 자동 전송
    poll_msg = f"📊 투표가 시작됐어요!\n질문: {question}\n" + "\n".join([f"  {i+1}. {o}" for i,o in enumerate(options)])
    if chat_type == 'public':
        PublicChat.objects.create(author=request.user, message=poll_msg)
    elif chat_type == 'group' and group:
        from .models import GroupChat
        GroupChat.objects.create(group=group, sender=request.user, message=poll_msg)

    return JsonResponse({
        'status': 'ok',
        'poll_id': poll.id,
        'question': question,
        'options': options,
    })

def chat_poll_vote(request, poll_id):
    """POST /chat/poll/<id>/vote/"""
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)

    import json
    data = json.loads(request.body)
    option = data.get('option', '').strip()

    poll = get_object_or_404(ChatPoll, pk=poll_id, is_active=True)

    if option not in poll.options:
        return JsonResponse({'error': '없는 선택지예요'}, status=400)

    # 기존 투표 제거 (한 사람 한 표)
    user_id = request.user.id
    votes = poll.votes
    for opt in votes:
        if user_id in votes[opt]:
            votes[opt].remove(user_id)

    # 새 투표 추가
    if option not in votes:
        votes[option] = []
    votes[option].append(user_id)
    poll.votes = votes
    poll.save()

    return JsonResponse({
        'status': 'ok',
        'results': poll.get_results(),
        'total': poll.total_votes,
    })

def chat_poll_list(request):
    """GET /chat/polls/?type=public&group_id=1"""
    from django.http import JsonResponse
    chat_type = request.GET.get('type', 'public')
    group_id = request.GET.get('group_id')

    polls = ChatPoll.objects.filter(chat_type=chat_type, is_active=True)
    if group_id:
        polls = polls.filter(group_id=int(group_id))
    polls = polls.order_by('-created_at')[:5]

    user_id = request.user.id if request.user.is_authenticated else None
    result = []
    for p in polls:
        my_vote = None
        for opt, voters in p.votes.items():
            if user_id in voters:
                my_vote = opt
                break
        result.append({
            'id': p.id,
            'question': p.question,
            'options': p.options,
            'results': p.get_results(),
            'total': p.total_votes,
            'my_vote': my_vote,
            'creator': p.creator.nickname or p.creator.username,
            'created_at': p.created_at.strftime('%H:%M'),
            'is_active': p.is_active,
        })

    return JsonResponse({'polls': result})


# ============================================================================
# 채팅 미니 투표
# ============================================================================
from .models import ChatPoll

def chat_poll_create(request):
    """POST /chat/poll/create/ - /투표 명령어 처리"""
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청'}, status=400)

    import json
    data = json.loads(request.body)
    question = data.get('question', '').strip()
    options = [o.strip() for o in data.get('options', []) if o.strip()]
    chat_type = data.get('chat_type', 'public')
    group_id = data.get('group_id')

    if not question or len(options) < 2:
        return JsonResponse({'error': '질문과 선택지 2개 이상을 입력해주세요'}, status=400)

    group = None
    if group_id:
        from .models import Group
        try:
            group = Group.objects.get(pk=int(group_id))
        except: pass

    poll = ChatPoll.objects.create(
        chat_type=chat_type,
        group=group,
        creator=request.user,
        question=question,
        options=options,
        votes={opt: [] for opt in options},
    )

    # 채팅방에 투표 생성 알림 메시지 자동 전송
    poll_msg = f"📊 투표가 시작됐어요!\n질문: {question}\n" + "\n".join([f"  {i+1}. {o}" for i,o in enumerate(options)])
    if chat_type == 'public':
        PublicChat.objects.create(author=request.user, message=poll_msg)
    elif chat_type == 'group' and group:
        from .models import GroupChat
        GroupChat.objects.create(group=group, sender=request.user, message=poll_msg)

    return JsonResponse({
        'status': 'ok',
        'poll_id': poll.id,
        'question': question,
        'options': options,
    })

def chat_poll_vote(request, poll_id):
    """POST /chat/poll/<id>/vote/"""
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)

    import json
    data = json.loads(request.body)
    option = data.get('option', '').strip()

    poll = get_object_or_404(ChatPoll, pk=poll_id, is_active=True)

    if option not in poll.options:
        return JsonResponse({'error': '없는 선택지예요'}, status=400)

    # 기존 투표 제거 (한 사람 한 표)
    user_id = request.user.id
    votes = poll.votes
    for opt in votes:
        if user_id in votes[opt]:
            votes[opt].remove(user_id)

    # 새 투표 추가
    if option not in votes:
        votes[option] = []
    votes[option].append(user_id)
    poll.votes = votes
    poll.save()

    return JsonResponse({
        'status': 'ok',
        'results': poll.get_results(),
        'total': poll.total_votes,
    })

def chat_poll_list(request):
    """GET /chat/polls/?type=public&group_id=1"""
    from django.http import JsonResponse
    chat_type = request.GET.get('type', 'public')
    group_id = request.GET.get('group_id')

    polls = ChatPoll.objects.filter(chat_type=chat_type, is_active=True)
    if group_id:
        polls = polls.filter(group_id=int(group_id))
    polls = polls.order_by('-created_at')[:5]

    user_id = request.user.id if request.user.is_authenticated else None
    result = []
    for p in polls:
        my_vote = None
        for opt, voters in p.votes.items():
            if user_id in voters:
                my_vote = opt
                break
        result.append({
            'id': p.id,
            'question': p.question,
            'options': p.options,
            'results': p.get_results(),
            'total': p.total_votes,
            'my_vote': my_vote,
            'creator': p.creator.nickname or p.creator.username,
            'created_at': p.created_at.strftime('%H:%M'),
            'is_active': p.is_active,
        })

    return JsonResponse({'polls': result})


def community_stats(request):
    """단지 통계 대시보드"""
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    from .models import CustomUser, Post, Comment, Survey, SurveyResponse, Event, Group, GroupMember, Letter, DirectMessage, PublicChat

    now = timezone.now()
    month_ago = now - timedelta(days=30)
    week_ago  = now - timedelta(days=7)

    # 회원
    total_users   = CustomUser.objects.filter(is_active=True).count()
    new_users     = CustomUser.objects.filter(date_joined__gte=month_ago).count()

    # 게시글/댓글
    total_posts    = Post.objects.count()
    week_posts     = Post.objects.filter(created_at__gte=week_ago).count()
    total_comments = Comment.objects.count()

    # 설문
    total_surveys   = Survey.objects.count()
    total_responses = SurveyResponse.objects.count()

    # 봉사
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(start_time__gte=now).count()

    # 소모임
    total_groups  = Group.objects.filter(is_active=True).count()
    total_members = GroupMember.objects.count()

    # 채팅 활성도 (최근 7일)
    week_public = PublicChat.objects.filter(created_at__gte=week_ago).count()
    week_dm     = DirectMessage.objects.filter(created_at__gte=week_ago).count()
    week_letter = Letter.objects.filter(created_at__gte=week_ago).count()

    # 활동 랭킹 TOP5 (게시글 기준)
    top_users = CustomUser.objects.annotate(
        post_count=Count("posts")
    ).order_by("-post_count")[:5]

    # 월별 신규 가입자 (최근 6개월)
    monthly_joins = []
    for i in range(5, -1, -1):
        d = now - timedelta(days=30*i)
        cnt = CustomUser.objects.filter(
            date_joined__year=d.year,
            date_joined__month=d.month
        ).count()
        monthly_joins.append({"month": d.strftime("%m월"), "count": cnt})

    # 설문 결과 - 참여자 수 높은 순으로 공개
    from django.db.models import Count as DCount
    surveys_by_response = Survey.objects.annotate(
        response_count=DCount('responses')
    ).filter(
        status__in=['active', 'closed']
    ).order_by('-response_count')[:10]

    return render(request, "stats_dashboard.html", {
        "total_users": total_users, "new_users": new_users,
        "total_posts": total_posts, "week_posts": week_posts,
        "total_comments": total_comments,
        "total_surveys": total_surveys, "total_responses": total_responses,
        "total_events": total_events, "upcoming_events": upcoming_events,
        "total_groups": total_groups, "total_members": total_members,
        "week_public": week_public, "week_dm": week_dm, "week_letter": week_letter,
        "top_users": top_users,
        "monthly_joins": monthly_joins,
        "surveys_by_response": surveys_by_response,
    })



# ============================================================
# 봉사활동 인증서 PDF 자동 발급
# ============================================================
@login_required
def my_certificate(request):
    """내 인증서 발급 페이지"""
    from .models import ActivityProof, Activity
    approved = ActivityProof.objects.filter(
        user=request.user, status='approved'
    ).select_related('activity').order_by('-submitted_at')
    total_points   = sum(a.points_earned for a in approved)
    total_hours    = sum(a.duration_hours or 0 for a in approved)
    total_count    = approved.count()
    return render(request, 'certificate.html', {
        'approved_activities': approved,
        'total_points':  total_points,
        'total_hours':   total_hours,
        'total_count':   total_count,
    })


@login_required
def certificate_pdf(request, user_id):
    """봉사활동 인증서 PDF 생성 및 다운로드"""
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import io, os
    from django.utils import timezone

    # 권한 체크 (본인 또는 관리자)
    if user_id != request.user.pk and not request.user.is_staff:
        from django.contrib import messages
        messages.error(request, '본인 인증서만 발급할 수 있습니다.')
        return redirect('my_certificate')

    target_user = get_object_or_404(CustomUser, pk=user_id)
    approved = ActivityProof.objects.filter(
        user=target_user, status='approved'
    ).select_related('activity').order_by('submitted_at')

    if not approved.exists():
        from django.contrib import messages
        messages.error(request, '승인된 활동이 없어 인증서를 발급할 수 없습니다.')
        return redirect('my_certificate')

    # 폰트 등록 (나눔고딕 없으면 기본 폰트 사용)
    font_name = 'Helvetica'
    font_bold = 'Helvetica-Bold'
    nanum_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    nanum_bold_path = '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'
    if os.path.exists(nanum_path):
        try:
            pdfmetrics.registerFont(TTFont('NanumGothic', nanum_path))
            pdfmetrics.registerFont(TTFont('NanumGothicBold', nanum_bold_path))
            font_name = 'NanumGothic'
            font_bold = 'NanumGothicBold'
        except:
            pass

    # PDF 생성
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )

    # 스타일
    styles = getSampleStyleSheet()
    title_style   = ParagraphStyle('title',   fontName=font_bold,  fontSize=26, alignment=TA_CENTER, textColor=colors.HexColor('#1a7a4a'), spaceAfter=4)
    sub_style     = ParagraphStyle('sub',     fontName=font_name,  fontSize=12, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=2)
    name_style    = ParagraphStyle('name',    fontName=font_bold,  fontSize=18, alignment=TA_CENTER, textColor=colors.HexColor('#1a3a2a'), spaceAfter=2)
    body_style    = ParagraphStyle('body',    fontName=font_name,  fontSize=11, alignment=TA_CENTER, spaceAfter=6)
    section_style = ParagraphStyle('section', fontName=font_bold,  fontSize=12, textColor=colors.HexColor('#1a7a4a'), spaceAfter=4)

    total_hours  = sum(a.duration_hours or 0 for a in approved)
    total_points = sum(a.points_earned for a in approved)
    total_count  = approved.count()
    issue_date   = timezone.now().strftime('%Y년 %m월 %d일')
    unit_info    = f"{target_user.dong}동 {target_user.ho}호" if target_user.dong else ""

    story = []

    # 헤더
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("🌿 봉사활동 인증서", title_style))
    story.append(Paragraph("VOLUNTEER CERTIFICATE", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a7a4a'), spaceAfter=8))
    story.append(Spacer(1, 5*mm))

    # 수상자 정보
    nickname = target_user.nickname or target_user.username
    story.append(Paragraph(f"{nickname} 님", name_style))
    if unit_info:
        story.append(Paragraph(unit_info, body_style))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"위 분은 해솔마을 7단지 지킴이 커뮤니티에서<br/>"
        f"총 <b>{total_count}회</b>의 봉사활동에 참여하여<br/>"
        f"<b>{total_hours}시간</b>의 봉사를 성실히 수행하셨기에<br/>"
        f"이 인증서를 드립니다.",
        body_style
    ))
    story.append(Spacer(1, 5*mm))

    # 요약 통계 표
    summary_data = [
        ['총 활동 횟수', '총 봉사 시간', '획득 포인트'],
        [f'{total_count}회', f'{total_hours}시간', f'{total_points}P'],
    ]
    summary_table = Table(summary_data, colWidths=[55*mm, 55*mm, 55*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), colors.HexColor('#1a7a4a')),
        ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
        ('FONTNAME',    (0,0), (-1,0), font_bold),
        ('FONTNAME',    (0,1), (-1,1), font_bold),
        ('FONTSIZE',    (0,0), (-1,-1), 12),
        ('ALIGN',       (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f0f8f4')]),
        ('GRID',        (0,0), (-1,-1), 0.5, colors.HexColor('#c8e6c9')),
        ('TOPPADDING',  (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0),(-1,-1), 8),
        ('ROUNDEDCORNERS', [3]),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 6*mm))

    # 활동 내역 표
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#c8e6c9'), spaceAfter=4))
    story.append(Paragraph("활동 내역", section_style))

    act_data = [['활동명', '날짜', '시간', '포인트']]
    for a in approved:
        act_data.append([
            Paragraph(a.activity.name if a.activity else '-', ParagraphStyle('td', fontName=font_name, fontSize=9)),
            a.submitted_at.strftime('%Y.%m.%d'),
            f"{a.duration_hours or 0}h",
            f"{a.points_earned}P",
        ])
    act_table = Table(act_data, colWidths=[80*mm, 35*mm, 25*mm, 25*mm])
    act_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0), colors.HexColor('#e8f5e9')),
        ('FONTNAME',     (0,0), (-1,0), font_bold),
        ('FONTNAME',     (0,1), (-1,-1), font_name),
        ('FONTSIZE',     (0,0), (-1,-1), 9),
        ('ALIGN',        (1,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.white, colors.HexColor('#f9fef9')]),
        ('GRID',         (0,0), (-1,-1), 0.3, colors.HexColor('#dcedc8')),
        ('TOPPADDING',   (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
    ]))
    story.append(act_table)
    story.append(Spacer(1, 8*mm))

    # 발급일 + 발급처
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1a7a4a'), spaceAfter=6))
    story.append(Paragraph(f"발급일: {issue_date}", body_style))
    story.append(Paragraph("해솔마을 7단지 지킴이 커뮤니티", ParagraphStyle('issuer', fontName=font_bold, fontSize=13, alignment=TA_CENTER, textColor=colors.HexColor('#1a7a4a'))))

    doc.build(story)
    buffer.seek(0)

    filename = f"봉사인증서_{nickname}_{timezone.now().strftime('%Y%m%d')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ============================================================
# 통합 캘린더 (봉사 + 소모임 + 단지행사)
# ============================================================
@login_required
def integrated_calendar(request):
    from .models import Meetup, Event, Group, CalendarEvent, GroupMember
    import json
    from django.db.models import Q

    user = request.user
    events = []

    # 내가 속한 소모임 ID 목록 + 내가 소모임장인 소모임
    my_group_ids = list(GroupMember.objects.filter(
        user=user, join_status='approved'
    ).values_list('group_id', flat=True))
    # 소모임장: creator이거나 GroupMember role='leader'
    my_leader_group_ids = list(set(
        list(Group.objects.filter(creator=user).values_list('id', flat=True)) +
        list(GroupMember.objects.filter(user=user, role='leader', join_status='approved').values_list('group_id', flat=True))
    ))

    # CalendarEvent 권한 기반 필터링
    # 볼 수 있는 조건:
    #   1. 내가 만든 것 (visibility 무관)
    #   2. 전체공개 승인완료
    #   3. 소모임공개 승인완료 + 내가 그 소모임 멤버
    #   4. 소모임공개 승인대기 + 내가 그 소모임장
    #   5. 전체공개 승인대기 + 내가 관리자
    ce_qs = CalendarEvent.objects.filter(
        Q(creator=user) |
        Q(visibility='public') |
        Q(visibility='group', group_id__in=my_group_ids) |
        Q(visibility='group_pending', group_id__in=my_leader_group_ids) |
        Q(visibility='pending', is_approved=False) if user.is_staff else Q(visibility='public') | Q(creator=user) | Q(visibility='group', group_id__in=my_group_ids)
    ).select_related('creator', 'group').distinct()

    if not user.is_staff:
        ce_qs = CalendarEvent.objects.filter(
            Q(creator=user) |
            Q(visibility='public') |
            Q(visibility='group', group_id__in=my_group_ids) |
            Q(visibility='group_pending', group_id__in=my_leader_group_ids)
        ).select_related('creator', 'group').distinct()

    color_map = {
        'personal':  '#6b7280',
        'volunteer': '#1a7a4a',
        'event':     '#7A263A',
        'group':     '#D4B26A',
    }
    icon_map = {
        'personal':  '🙋',
        'volunteer': '🤝',
        'event':     '📅',
        'group':     '👥',
    }
    badge_map = {
        'private':       '🔒',
        'group_pending': '⏳',
        'group':         '👥',
        'pending':       '⏳',
        'public':        '',
    }

    for ce in ce_qs:
        color  = ce.color if ce.color else color_map.get(ce.event_type, '#6b7280')
        icon   = icon_map.get(ce.event_type, '📌')
        badge  = badge_map.get(ce.visibility, '')
        is_pending = ce.visibility in ('pending', 'group_pending')
        if is_pending:
            color = '#9ca3af'
        if ce.visibility == 'private' and not ce.color:
            color = '#6b7280'

        ev = {
            'id':              f'ce_{ce.id}',
            'title':           f'{badge}{icon} {ce.title}',
            'start':           ce.start_time.isoformat(),
            'end':             ce.end_time.isoformat() if ce.end_time else None,
            'backgroundColor': color,
            'borderColor':     color,
            'extendedProps': {
                'cal_id':      ce.id,
                'type':        ce.get_event_type_display(),
                'visibility':  ce.visibility,
                'vis_label':   ce.get_visibility_display(),
                'location':    ce.location,
                'description': ce.description,
                'creator':     ce.creator.nickname or ce.creator.username,
                'creator_id':  ce.creator.id,
                'group':       ce.group.name if ce.group else None,
                'group_id':    ce.group.id if ce.group else None,
                'is_mine':     ce.creator == user,
                'is_pending':  is_pending,
                'can_approve': (
                    (ce.visibility == 'pending' and user.is_staff) or
                    (ce.visibility == 'group_pending' and ce.group_id in my_leader_group_ids)
                ),
            }
        }
        # RRule 반복 설정
        if ce.rrule:
            # dtstart를 KST 로컬시간으로 명시 (FullCalendar timeZone과 일치)
            from django.utils import timezone as tz
            from django.utils import timezone as _tz
            kst_start = ce.start_time.astimezone(_tz.get_current_timezone())
            dtstart = kst_start.strftime('%Y%m%dT%H%M%S')
            ev['rrule']    = 'DTSTART:' + dtstart + '\n' + ce.rrule
            ev['duration'] = None
            if ce.end_time:
                delta = ce.end_time - ce.start_time
                h, s  = divmod(int(delta.total_seconds()), 3600)
                m     = s // 60
                ev['duration'] = f'{h:02d}:{m:02d}'
        events.append(ev)

    # 봉사활동
    meetups = Meetup.objects.filter(
        is_confirmed=True,
        status__in=['recruiting', 'confirmed'],
        scheduled_at__isnull=False,
    ).select_related('creator')
    for m in meetups:
        events.append({
            'id': f'meetup_{m.id}',
            'title': f'🤝 {m.title}',
            'start': m.scheduled_at.isoformat(),
            'url': f'/volunteer/{m.id}/',
            'backgroundColor': '#1a7a4a',
            'borderColor': '#1a7a4a',
            'extendedProps': {'type': '봉사활동', 'location': m.location, 'cal_id': None}
        })

    # 단지행사
    for e in Event.objects.filter(start_time__isnull=False).select_related('post'):
        events.append({
            'id': f'event_{e.id}',
            'title': f'📢 {e.post.title}',
            'start': e.start_time.isoformat(),
            'end': e.end_time.isoformat() if e.end_time else None,
            'url': f'/posts/{e.post.id}/',
            'backgroundColor': '#7A263A',
            'borderColor': '#7A263A',
            'extendedProps': {'type': '단지행사', 'location': e.location, 'cal_id': None}
        })

    # 내 소모임 목록 (등록 모달용)
    my_groups = list(Group.objects.filter(id__in=my_group_ids).values('id', 'name'))
    is_leader = len(my_leader_group_ids) > 0

    return render(request, 'integrated_calendar.html', {
        'events_json':         json.dumps(events, ensure_ascii=False, default=str),
        'my_groups_json':      json.dumps(my_groups, ensure_ascii=False),
        'my_leader_group_ids': json.dumps(my_leader_group_ids),
        'total_events':        len(events),
        'is_leader':           is_leader,
    })
def error_404(request, exception=None):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)


# ============================================================================
# 캘린더 일정 등록/수정/삭제/승인 API
# ============================================================================
@login_required
def calendar_event_create(request):
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청'}, status=400)
    import json
    from .models import CalendarEvent, Group, GroupMember, Notification
    from django.utils import timezone
    from django.utils.dateparse import parse_datetime

    data       = json.loads(request.body)
    user       = request.user
    event_type = data.get('event_type', 'personal')
    group_id   = data.get('group_id')
    visibility = data.get('visibility', 'private')  # 사용자가 선택한 공개범위
    group      = None

    if group_id:
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return JsonResponse({'error': '소모임을 찾을 수 없습니다'}, status=404)

    # 권한 검증 및 실제 visibility 결정
    # 사용자가 선택한 visibility를 기반으로, 권한에 따라 즉시승인 or 승인대기 처리
    is_approved       = False
    approved_by       = None
    approved_at       = None
    final_visibility  = visibility
    notify_targets    = []  # 알림 보낼 대상
    approval_note     = ''  # 사용자에게 보여줄 안내

    if visibility == 'private':
        # 나만보기: 항상 즉시
        is_approved      = True
        approved_by      = user
        approved_at      = timezone.now()
        final_visibility = 'private'
        approval_note    = '나만 볼 수 있는 개인 일정입니다.'

    elif visibility == 'group':
        # 소모임공개: 소모임장이면 즉시, 아니면 승인대기
        is_group_leader = group and (group.creator == user or GroupMember.objects.filter(group=group, user=user, role='leader', join_status='approved').exists())
        if is_group_leader or user.is_staff:
            is_approved      = True
            approved_by      = user
            approved_at      = timezone.now()
            final_visibility = 'group'
            approval_note    = '소모임 멤버에게 즉시 공개됩니다.'
        else:
            final_visibility = 'group_pending'
            approval_note    = '소모임장 승인 후 멤버에게 공개됩니다.'
            if group:
                # 소모임장에게 알림 (creator + role=leader 멤버)
                leaders = set()
                leaders.add(group.creator)
                for lm in GroupMember.objects.filter(group=group, role='leader', join_status='approved').select_related('user'):
                    leaders.add(lm.user)
                for leader in leaders:
                    notify_targets.append(('group_leader', leader))

    elif visibility == 'public':
        # 전체공개: 관리자면 즉시, 아니면 승인대기
        if user.is_staff or user.is_superuser:
            is_approved      = True
            approved_by      = user
            approved_at      = timezone.now()
            final_visibility = 'public'
            approval_note    = '즉시 전체 공개됩니다.'
        else:
            final_visibility = 'pending'
            approval_note    = '관리자 승인 후 전체 공개됩니다.'
            from django.contrib.auth import get_user_model
            User = get_user_model()
            for admin in User.objects.filter(is_staff=True):
                notify_targets.append(('admin', admin))

    # RRule 생성
    rrule          = ''
    recur_interval = 1
    recur_type     = data.get('recur_type', '')
    if data.get('is_recurring') and recur_type and recur_type != 'none':
        recur_interval = int(data.get('recur_interval', 1))
        recur_end      = data.get('recur_end_date', '')
        freq_map       = {'daily': 'DAILY', 'weekly': 'WEEKLY', 'monthly': 'MONTHLY'}
        freq           = freq_map.get(recur_type, 'WEEKLY')
        # UNTIL을 KST 종료일 23:59:59 기준으로 설정 (UTC 변환: -9시간 = 전날 14:59:59)
        until = recur_end.replace('-', '') + 'T145959Z' if recur_end else ''
        rrule = f'FREQ={freq};INTERVAL={recur_interval}'
        if until:
            rrule += f';UNTIL={until}'

    start_dt = parse_datetime(data.get('start_time'))
    end_dt   = parse_datetime(data.get('end_time')) if data.get('end_time') else None

    # timezone aware 처리
    from django.utils.timezone import make_aware, is_naive
    if start_dt and is_naive(start_dt):
        start_dt = make_aware(start_dt)
    if end_dt and is_naive(end_dt):
        end_dt = make_aware(end_dt)

    event = CalendarEvent.objects.create(
        title          = data.get('title', '').strip(),
        description    = data.get('description', '').strip(),
        event_type     = event_type,
        start_time     = start_dt,
        end_time       = end_dt,
        location       = data.get('location', '').strip(),
        creator        = user,
        group          = group,
        visibility     = final_visibility,
        is_approved    = is_approved,
        approved_by    = approved_by,
        approved_at    = approved_at,
        rrule          = rrule,
        recur_interval = recur_interval,
        color          = data.get('color', ''),
        all_day        = data.get('all_day', False),
    )

    # 승인 요청 알림 발송
    for ntype, target in notify_targets:
        try:
            if ntype == 'group_leader':
                msg = f'📅 {user.nickname or user.username}님이 [{group.name}] 소모임 일정 승인을 요청했습니다: {event.title}'
            else:
                msg = f'📅 {user.nickname or user.username}님이 전체공개 일정 승인을 요청했습니다: {event.title}'
            Notification.objects.create(
                recipient=target,
                sender=user,
                notification_type='calendar_approval',
                message=msg,
                link=f'/calendar/',
            )
        except Exception:
            pass

    return JsonResponse({
        'success':      True,
        'id':           event.id,
        'visibility':   final_visibility,
        'approval_note': approval_note,
    })


@login_required
def post_image_upload(request):
    """Quill 에디터 이미지 서버 업로드 API"""
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청'}, status=400)
    image = request.FILES.get('image')
    if not image:
        return JsonResponse({'error': '이미지가 없습니다'}, status=400)
    import uuid, os
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    from django.utils import timezone
    now = timezone.now()
    ext = os.path.splitext(image.name)[1].lower() or '.jpg'
    # 경로 직접 지정 (upload_to 우회 - 중복 방지)
    save_path = f'posts/{now.year}/{now.month:02d}/{uuid.uuid4().hex[:12]}{ext}'
    path = default_storage.save(save_path, ContentFile(image.read()))
    url  = default_storage.url(path)
    return JsonResponse({'success': True, 'url': url})


@login_required
def group_calendar_events(request, pk):
    """소모임 캘린더 이벤트 JSON API"""
    import json
    from .models import CalendarEvent, Group, GroupMember
    from django.db.models import Q

    try:
        group = Group.objects.get(pk=pk)
    except Group.DoesNotExist:
        return JsonResponse({'error': '소모임 없음'}, status=404)

    user = request.user
    my_group_ids = list(GroupMember.objects.filter(user=user, join_status='approved').values_list('group_id', flat=True))
    is_leader = (
        group.creator == user or
        GroupMember.objects.filter(group=group, user=user, role='leader', join_status='approved').exists()
    )

    events = []
    ce_qs = CalendarEvent.objects.filter(
        group=group,
        visibility__in=['group', 'group_pending', 'public']
    ).select_related('creator', 'group')

    color_map = {'personal':'#6b7280','volunteer':'#1a7a4a','event':'#7A263A','group':'#D4B26A'}
    badge_map = {'group_pending':'⏳','group':'','public':'','pending':'⏳','private':'🔒'}

    for ce in ce_qs:
        color     = ce.color if ce.color else color_map.get(ce.event_type, '#6b7280')
        is_pending = ce.visibility == 'group_pending'
        if is_pending: color = '#9ca3af'
        badge = badge_map.get(ce.visibility, '')

        ev = {
            'id':              f'ce_{ce.id}',
            'title':           f'{badge} {ce.title}'.strip(),
            'start':           ce.start_time.isoformat(),
            'end':             ce.end_time.isoformat() if ce.end_time else None,
            'allDay':          ce.all_day,
            'backgroundColor': color,
            'borderColor':     color,
            'extendedProps': {
                'cal_id':      ce.id,
                'type':        ce.get_event_type_display(),
                'visibility':  ce.visibility,
                'location':    ce.location,
                'description': ce.description,
                'creator':     ce.creator.nickname or ce.creator.username,
                'creator_id':  ce.creator.id,
                'is_mine':     ce.creator == user,
                'can_approve': is_pending and is_leader,
                'can_edit':    ce.creator == user or is_leader or user.is_staff,
            }
        }
        if ce.rrule:
            from django.utils import timezone as _tz
            kst_start = ce.start_time.astimezone(_tz.get_current_timezone())
            dtstart = kst_start.strftime('%Y%m%dT%H%M%S')
            ev['rrule'] = 'DTSTART:' + dtstart + '\n' + ce.rrule
            if ce.end_time:
                delta = ce.end_time - ce.start_time
                h, s  = divmod(int(delta.total_seconds()), 3600)
                m     = s // 60
                ev['duration'] = f'{h:02d}:{m:02d}'
        events.append(ev)

    return JsonResponse({
        'events':    events,
        'is_leader': is_leader,
        'group_id':  pk,
        'group_name': group.name,
    })


@login_required
def calendar_event_detail(request, pk):
    from .models import CalendarEvent, CalendarEventAttendee, CalendarEventComment, GroupMember
    from django.db.models import Q
    try:
        event = CalendarEvent.objects.get(id=pk)
    except CalendarEvent.DoesNotExist:
        from django.http import Http404
        raise Http404

    user = request.user
    # 접근 권한 체크
    my_group_ids = list(GroupMember.objects.filter(user=user, join_status='approved').values_list('group_id', flat=True))
    can_view = (
        event.visibility == 'public' or
        event.creator == user or
        (event.visibility == 'group' and event.group_id in my_group_ids) or
        (event.visibility == 'private' and event.creator == user) or
        user.is_staff
    )
    if not can_view:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    attendees   = event.attendees.select_related('user').all()
    comments    = event.comments.select_related('author').all()
    my_attend   = attendees.filter(user=user).first() if user.is_authenticated else None
    attend_count = attendees.filter(status='attending').count()

    is_leader = (
        event.group and (
            event.group.creator == user or
            GroupMember.objects.filter(group=event.group, user=user, role='leader', join_status='approved').exists()
        )
    ) if event.group else False
    can_edit = event.creator == user or is_leader or user.is_staff

    return render(request, 'calendar_event_detail.html', {
        'event':        event,
        'attendees':    attendees,
        'comments':     comments,
        'my_attend':    my_attend,
        'attend_count': attend_count,
        'can_edit':     can_edit,
    })


@login_required
def calendar_event_attend(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청'}, status=400)
    import json
    from .models import CalendarEvent, CalendarEventAttendee
    try:
        event = CalendarEvent.objects.get(id=pk)
    except CalendarEvent.DoesNotExist:
        return JsonResponse({'error': '일정 없음'}, status=404)

    data   = json.loads(request.body)
    status = data.get('status', 'attending')
    obj, created = CalendarEventAttendee.objects.update_or_create(
        event=event, user=request.user,
        defaults={'status': status}
    )
    attend_count = event.attendees.filter(status='attending').count()
    return JsonResponse({'success': True, 'status': status, 'attend_count': attend_count})


@login_required
def calendar_event_comment(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청'}, status=400)
    import json
    from .models import CalendarEvent, CalendarEventComment
    try:
        event = CalendarEvent.objects.get(id=pk)
    except CalendarEvent.DoesNotExist:
        return JsonResponse({'error': '일정 없음'}, status=404)

    data    = json.loads(request.body)
    content = data.get('content', '').strip()
    if not content:
        return JsonResponse({'error': '내용을 입력해주세요'}, status=400)

    comment = CalendarEventComment.objects.create(
        event=event, author=request.user, content=content
    )
    return JsonResponse({
        'success':    True,
        'id':         comment.id,
        'content':    comment.content,
        'author':     comment.author.nickname or comment.author.username,
        'created_at': comment.created_at.strftime('%m/%d %H:%M'),
    })


@login_required
def calendar_event_comment_delete(request, pk, comment_pk):
    from .models import CalendarEventComment
    try:
        comment = CalendarEventComment.objects.get(id=comment_pk, event_id=pk)
    except CalendarEventComment.DoesNotExist:
        return JsonResponse({'error': '댓글 없음'}, status=404)
    if comment.author != request.user and not request.user.is_staff:
        return JsonResponse({'error': '권한 없음'}, status=403)
    comment.delete()
    return JsonResponse({'success': True})


@login_required
def calendar_event_edit(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청'}, status=400)
    import json
    from .models import CalendarEvent, GroupMember
    from django.utils.dateparse import parse_datetime
    from django.utils.timezone import make_aware, is_naive

    try:
        event = CalendarEvent.objects.get(id=pk)
    except CalendarEvent.DoesNotExist:
        return JsonResponse({'error': '일정을 찾을 수 없습니다'}, status=404)

    user = request.user
    is_leader = (
        event.group and (
            event.group.creator == user or
            GroupMember.objects.filter(group=event.group, user=user, role='leader', join_status='approved').exists()
        )
    )
    if event.creator != user and not is_leader and not user.is_staff:
        return JsonResponse({'error': '권한이 없습니다'}, status=403)

    data = json.loads(request.body)
    start_dt = parse_datetime(data.get('start_time', ''))
    end_dt   = parse_datetime(data.get('end_time', '')) if data.get('end_time') else None
    if start_dt and is_naive(start_dt): start_dt = make_aware(start_dt)
    if end_dt   and is_naive(end_dt):   end_dt   = make_aware(end_dt)

    event.title       = data.get('title', event.title).strip()
    event.description = data.get('description', event.description).strip()
    event.location    = data.get('location', event.location).strip()
    if start_dt: event.start_time = start_dt
    if end_dt:   event.end_time   = end_dt
    event.save()
    return JsonResponse({'success': True})


@login_required
def calendar_event_delete(request, pk):
    from .models import CalendarEvent
    try:
        event = CalendarEvent.objects.get(id=pk)
    except CalendarEvent.DoesNotExist:
        return JsonResponse({'error': '일정을 찾을 수 없습니다'}, status=404)

    if event.creator != request.user and not request.user.is_staff:
        return JsonResponse({'error': '권한이 없습니다'}, status=403)

    event.delete()
    return JsonResponse({'success': True})


@login_required
def calendar_event_approve(request, pk):
    from .models import CalendarEvent, Notification
    from django.utils import timezone
    try:
        event = CalendarEvent.objects.get(id=pk)
    except CalendarEvent.DoesNotExist:
        return JsonResponse({'error': '일정을 찾을 수 없습니다'}, status=404)

    user = request.user

    # 소모임장 승인
    if event.visibility == 'group_pending':
        is_leader = event.group and (
            event.group.creator == user or
            GroupMember.objects.filter(group=event.group, user=user, role='leader', join_status='approved').exists()
        )
        if not is_leader and not user.is_staff:
            return JsonResponse({'error': '소모임장 권한이 필요합니다'}, status=403)
        event.visibility         = 'group'
        event.is_approved        = True
        event.group_approved_by  = user
        event.group_approved_at  = timezone.now()
        event.save()
        try:
            Notification.objects.create(
                recipient=event.creator, sender=user,
                notification_type='calendar_approved',
                message=f'✅ 소모임 일정이 승인됐습니다: {event.title}',
                link='/calendar/',
            )
        except Exception:
            pass
        return JsonResponse({'success': True, 'visibility': 'group'})

    # 관리자 승인
    if event.visibility == 'pending':
        if not user.is_staff and not user.is_superuser:
            return JsonResponse({'error': '관리자 권한이 필요합니다'}, status=403)
        event.visibility  = 'public'
        event.is_approved = True
        event.approved_by = user
        event.approved_at = timezone.now()
        event.save()
        try:
            Notification.objects.create(
                recipient=event.creator, sender=user,
                notification_type='calendar_approved',
                message=f'✅ 일정이 전체 공개 승인됐습니다: {event.title}',
                link='/calendar/',
            )
        except Exception:
            pass
        return JsonResponse({'success': True, 'visibility': 'public'})

    return JsonResponse({'error': '승인할 수 없는 상태입니다'}, status=400)


# ════════════════════════════════════════════════════════
# 비밀번호 찾기 (보안질문 + 이메일)
# ════════════════════════════════════════════════════════
import json as _json
import secrets as _secrets
from django.core.cache import cache as _cache
from django.http import JsonResponse as _JR

def password_reset_page(request):
    """비밀번호 찾기 메인 페이지"""
    return render(request, 'registration/password_reset.html')

def pw_get_question(request):
    """AJAX: 아이디+실명 확인 후 보안 질문 반환"""
    if request.method != 'POST':
        return _JR({'ok': False, 'error': '잘못된 요청'})
    try:
        data      = _json.loads(request.body)
        username  = data.get('username', '').strip()
        real_name = data.get('real_name', '').strip()
        user = CustomUser.objects.get(username=username)
        # 실명 확인 (대소문자 무관)
        if user.real_name.strip().lower() != real_name.lower():
            return _JR({'ok': False, 'error': '아이디 또는 실명이 일치하지 않습니다.'})
        if not user.security_question:
            return _JR({'ok': False, 'error': '보안 질문이 등록되지 않은 계정입니다. 이메일로 찾기를 이용해주세요.'})
        return _JR({'ok': True, 'question': user.security_question})
    except CustomUser.DoesNotExist:
        return _JR({'ok': False, 'error': '아이디 또는 실명이 일치하지 않습니다.'})
    except Exception as e:
        return _JR({'ok': False, 'error': '오류가 발생했습니다.'})

def pw_verify_answer(request):
    """AJAX: 보안 답변 검증 후 리셋 토큰 발급"""
    if request.method != 'POST':
        return _JR({'ok': False, 'error': '잘못된 요청'})
    try:
        data     = _json.loads(request.body)
        username = data.get('username', '').strip()
        answer   = data.get('answer', '').strip().lower()
        user = CustomUser.objects.get(username=username)
        if user.security_answer.strip().lower() != answer:
            return _JR({'ok': False, 'error': '답변이 일치하지 않습니다.'})
        # 10분 유효 토큰 발급
        token = _secrets.token_urlsafe(32)
        _cache.set(f'pw_reset_{token}', user.pk, timeout=600)
        return _JR({'ok': True, 'token': token})
    except CustomUser.DoesNotExist:
        return _JR({'ok': False, 'error': '사용자를 찾을 수 없습니다.'})
    except Exception:
        return _JR({'ok': False, 'error': '오류가 발생했습니다.'})

def pw_do_reset(request):
    """AJAX: 토큰 검증 후 비밀번호 변경"""
    if request.method != 'POST':
        return _JR({'ok': False, 'error': '잘못된 요청'})
    try:
        data     = _json.loads(request.body)
        token    = data.get('token', '')
        password = data.get('password', '')
        if len(password) < 8:
            return _JR({'ok': False, 'error': '비밀번호는 8자 이상이어야 해요.'})
        user_pk = _cache.get(f'pw_reset_{token}')
        if not user_pk:
            return _JR({'ok': False, 'error': '세션이 만료됐습니다. 처음부터 다시 시도해주세요.'})
        user = CustomUser.objects.get(pk=user_pk)
        user.set_password(password)
        user.save()
        _cache.delete(f'pw_reset_{token}')
        return _JR({'ok': True})
    except CustomUser.DoesNotExist:
        return _JR({'ok': False, 'error': '사용자를 찾을 수 없습니다.'})
    except Exception:
        return _JR({'ok': False, 'error': '오류가 발생했습니다.'})

def pw_send_email(request):
    """AJAX: 이메일로 비밀번호 재설정 링크 발송"""
    if request.method != 'POST':
        return _JR({'ok': False, 'error': '잘못된 요청'})
    try:
        data     = _json.loads(request.body)
        username = data.get('username', '').strip()
        email    = data.get('email', '').strip().lower()
        # 보안상 항상 ok 반환 (사용자 존재 여부 노출 방지)
        try:
            user = CustomUser.objects.get(username=username)
            if user.email.lower() == email:
                token = _secrets.token_urlsafe(32)
                _cache.set(f'pw_reset_{token}', user.pk, timeout=1800)  # 30분
                reset_url = f"{request.scheme}://{request.get_host()}/accounts/password-reset/email-confirm/?token={token}"
                from django.core.mail import send_mail
                send_mail(
                    subject='[해솔7 지킴이] 비밀번호 재설정',
                    message=f"""안녕하세요, {user.nickname or user.username}님.\n\n비밀번호 재설정을 요청하셨습니다.\n아래 링크를 클릭해 새 비밀번호를 설정해주세요.\n\n{reset_url}\n\n링크는 30분간 유효합니다.\n요청하지 않으셨다면 이 메일을 무시해주세요.\n\n해솔7 지킴이 드림""",
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
        except CustomUser.DoesNotExist:
            pass
    except Exception:
        pass
    return _JR({'ok': True})  # 항상 성공 반환

def pw_email_confirm(request):
    """이메일 링크 클릭 후 새 비밀번호 설정 페이지"""
    token = request.GET.get('token', '')
    user_pk = _cache.get(f'pw_reset_{token}')
    if not user_pk:
        messages.error(request, '링크가 만료됐거나 유효하지 않습니다.')
        return redirect('password_reset_page')
    if request.method == 'POST':
        pw1 = request.POST.get('password1', '')
        pw2 = request.POST.get('password2', '')
        if len(pw1) < 8:
            messages.error(request, '비밀번호는 8자 이상이어야 해요.')
        elif pw1 != pw2:
            messages.error(request, '비밀번호가 일치하지 않아요.')
        else:
            try:
                user = CustomUser.objects.get(pk=user_pk)
                user.set_password(pw1)
                user.save()
                _cache.delete(f'pw_reset_{token}')
                messages.success(request, '비밀번호가 변경됐어요! 새 비밀번호로 로그인해주세요.')
                return redirect('login')
            except CustomUser.DoesNotExist:
                messages.error(request, '오류가 발생했습니다.')
    return render(request, 'registration/pw_email_confirm.html', {'token': token})


# ════════════════════════════════════════════════════════════════════
# 관리자 전용 — 회원 등급 관리 + 비밀번호 초기화
# 개인정보보호법 29조: 관리자 행위 전건 로그 기록
# ════════════════════════════════════════════════════════════════════
from django.contrib.admin.views.decorators import staff_member_required as _staff
import random as _rand, string as _str, json as _json
from django.core.mail import send_mail as _send_mail
from django.core.cache import cache as _cache
import secrets as _secrets

def _get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR')

def _log_action(admin, target, action, detail, ip):
    """관리자 행위 로그 기록 — 평문 비밀번호 절대 포함 금지"""
    from .models import AdminActionLog
    AdminActionLog.objects.create(
        admin=admin, target_user=target,
        action=action, detail=detail, ip_address=ip
    )

@_staff
def admin_member_manage(request):
    """회원 등급 관리 + 비밀번호 초기화 메인 페이지"""
    from .models import MemberGrade, AdminActionLog

    q      = request.GET.get('q', '').strip()
    grade  = request.GET.get('grade', '')
    status = request.GET.get('status', '')

    users = CustomUser.objects.all().order_by('-date_joined')
    if q:
        from django.db.models import Q
        users = users.filter(
            Q(username__icontains=q) | Q(nickname__icontains=q) |
            Q(real_name__icontains=q) | Q(dong__icontains=q)
        )
    if status == 'active':   users = users.filter(is_active=True)
    if status == 'inactive': users = users.filter(is_active=False)
    if status == 'verified': users = users.filter(is_verified=True)
    if status == 'unverified': users = users.filter(is_verified=False)

    grades      = MemberGrade.objects.filter(is_active=True).order_by('order')
    recent_logs = AdminActionLog.objects.select_related('admin','target_user')[:20]

    return render(request, 'admin/member_manage.html', {
        'users': users, 'grades': grades,
        'recent_logs': recent_logs,
        'q': q, 'grade': grade, 'status': status,
        'total': CustomUser.objects.count(),
        'active_count': CustomUser.objects.filter(is_active=True).count(),
        'verified_count': CustomUser.objects.filter(is_verified=True).count(),
    })

@_staff
def admin_pw_reset(request):
    """비밀번호 초기화 — 임시 비밀번호 이메일 발송"""
    if request.method != 'POST':
        return redirect('admin_member_manage')

    user_id = request.POST.get('user_id')
    ip      = _get_client_ip(request)

    try:
        target = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, '사용자를 찾을 수 없습니다.')
        return redirect('admin_member_manage')

    # 이메일 없으면 발급 불가 (개인정보 노출 방지)
    if not target.email:
        messages.error(
            request,
            f'⚠ {target.nickname or target.username}님의 이메일이 등록되지 않아 발급할 수 없습니다.'
        )
        return redirect('admin_member_manage')

    # 임시 비밀번호 생성 (영문 대소문자 + 숫자 10자리)
    chars  = _str.ascii_letters + _str.digits
    tmp_pw = ''.join(_rand.choices(chars, k=10))

    # DB에 해시만 저장 (평문 절대 저장 금지)
    target.set_password(tmp_pw)
    target.save(update_fields=['password'])

    # 사용자에게 이메일 발송
    try:
        _send_mail(
            subject='[해솔7 지킴이] 임시 비밀번호가 발급됐어요',
            message=(
                f"{target.nickname or target.username}님, 안녕하세요.\n\n"
                f"관리자가 회원님의 비밀번호를 초기화했습니다.\n\n"
                f"임시 비밀번호: {tmp_pw}\n\n"
                f"보안을 위해 로그인 후 즉시 비밀번호를 변경해주세요.\n"
                f"비밀번호 변경: {request.scheme}://{request.get_host()}/mypage/edit/\n\n"
                f"본인이 요청하지 않은 경우 즉시 관리자에게 문의해주세요.\n\n"
                f"해솔7 지킴이 드림"
            ),
            from_email=None,
            recipient_list=[target.email],
            fail_silently=False,
        )
        email_sent = True
    except Exception as e:
        email_sent = False

    # ★ 관리자 행위 로그 기록 (평문 비밀번호 절대 포함 금지)
    _log_action(
        admin=request.user,
        target=target,
        action='pw_reset',
        detail=f"이메일 발송{'성공' if email_sent else '실패'} | 수신: {target.email[:3]}***",
        ip=ip
    )

    if email_sent:
        messages.success(
            request,
            f"✅ {target.nickname or target.username}님의 임시 비밀번호를 이메일({target.email[:3]}***)로 발송했습니다."
        )
    else:
        messages.warning(
            request,
            f"⚠ 비밀번호는 초기화됐으나 이메일 발송에 실패했습니다. 이메일 설정을 확인해주세요."
        )
    return redirect('admin_member_manage')

@_staff
def admin_grade_change(request):
    """회원 등급 변경"""
    if request.method != 'POST':
        return redirect('admin_member_manage')

    from .models import MemberGrade
    user_id  = request.POST.get('user_id')
    grade_id = request.POST.get('grade_id')
    ip       = _get_client_ip(request)

    try:
        target     = CustomUser.objects.get(pk=user_id)
        new_grade  = MemberGrade.objects.get(pk=grade_id)
        old_groups = list(target.groups.values_list('name', flat=True))

        # 기존 등급 그룹 제거 후 새 등급 추가
        from django.contrib.auth.models import Group as AuthGroup
        grade_names = MemberGrade.objects.values_list('name', flat=True)
        for g in target.groups.filter(name__in=grade_names):
            target.groups.remove(g)
        new_group, _ = AuthGroup.objects.get_or_create(name=new_grade.name)
        target.groups.add(new_group)

        _log_action(
            admin=request.user, target=target,
            action='grade_change',
            detail=f"{old_groups} → {new_grade.name}",
            ip=ip
        )
        messages.success(request, f"✅ {target.nickname or target.username}님 등급을 [{new_grade.name}](으)로 변경했습니다.")
    except (CustomUser.DoesNotExist, MemberGrade.DoesNotExist):
        messages.error(request, '사용자 또는 등급을 찾을 수 없습니다.')

    return redirect('admin_member_manage')

@_staff
def admin_toggle_active(request):
    """계정 활성/비활성 토글"""
    if request.method != 'POST':
        return redirect('admin_member_manage')

    user_id = request.POST.get('user_id')
    ip      = _get_client_ip(request)

    try:
        target = CustomUser.objects.get(pk=user_id)
        if target.is_superuser:
            messages.error(request, '최고관리자 계정은 변경할 수 없습니다.')
            return redirect('admin_member_manage')

        target.is_active = not target.is_active
        target.save(update_fields=['is_active'])

        action = 'activate' if target.is_active else 'deactivate'
        _log_action(admin=request.user, target=target, action=action, detail='', ip=ip)

        status = '활성화' if target.is_active else '비활성화'
        messages.success(request, f"✅ {target.nickname or target.username}님 계정을 {status}했습니다.")
    except CustomUser.DoesNotExist:
        messages.error(request, '사용자를 찾을 수 없습니다.')

    return redirect('admin_member_manage')

@_staff
def admin_action_log(request):
    """관리자 행위 로그 전체 조회"""
    from .models import AdminActionLog
    logs = AdminActionLog.objects.select_related('admin','target_user').all()
    action_filter = request.GET.get('action','')
    if action_filter:
        logs = logs.filter(action=action_filter)
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 30)
    page = paginator.get_page(request.GET.get('page', 1))
    from .models import AdminActionLog as AL
    return render(request, 'admin/action_log.html', {
        'page': page, 'action_filter': action_filter,
        'action_choices': AL.ACTION_CHOICES,
    })


# ════════════════════════════════════════════════════════
# 배지 자동 발급 로직
# ════════════════════════════════════════════════════════
def _auto_award_badges(user):
    """봉사 승인 시 배지 자동 발급"""
    from .models import Badge, UserBadge
    approved_count = ActivityProof.objects.filter(
        user=user, status='approved'
    ).count()
    total_points = user.mileage_points

    badges = Badge.objects.filter(is_active=True)
    for badge in badges:
        already_has = UserBadge.objects.filter(user=user, badge=badge).exists()
        if already_has:
            continue
        # 조건 충족 여부 확인
        if approved_count >= badge.required_activities and            total_points >= badge.required_points:
            UserBadge.objects.create(user=user, badge=badge)
            Notification.objects.create(
                recipient=user,
                title=f"🏅 새 배지 획득!",
                message=f"축하해요! '{badge.title}' 배지를 획득했어요!",
                notification_type='badge',
            )


# ============================================================================
# 친구/팔로우
# ============================================================================
@login_required
def follow_user(request, user_id):
    from .models import UserFollow, Notification
    target = get_object_or_404(CustomUser, pk=user_id)
    if target == request.user:
        messages.error(request, '자기 자신을 팔로우할 수 없어요.')
        return redirect('user_profile', user_id=user_id)

    follow, created = UserFollow.objects.get_or_create(
        follower=request.user, following=target
    )
    if not created:
        follow.delete()
        messages.info(request, f'{target.nickname or target.username}님 팔로우를 취소했어요.')
    else:
        messages.success(request, f'{target.nickname or target.username}님을 팔로우했어요!')
        # 맞팔이면 친구 알림
        if UserFollow.is_friend(request.user, target):
            Notification.objects.create(
                recipient=target,
                title='새 친구!',
                message=f'{request.user.nickname or request.user.username}님과 친구가 됐어요! 🎉',
                notification_type='community',
            )
    return redirect('user_profile', user_id=user_id)


@login_required
def friend_list(request):
    from .models import UserFollow
    friends  = UserFollow.get_friends(request.user)
    following = UserFollow.objects.filter(follower=request.user).select_related('following')
    followers = UserFollow.objects.filter(following=request.user).select_related('follower')
    return render(request, 'friend_list.html', {
        'friends':   friends,
        'following': following,
        'followers': followers,
    })


# ============================================================================
# 소모임 유저 검색 + 초대
# ============================================================================
@login_required
def group_invite(request, pk):
    """닉네임/ID로 유저 검색 후 소모임 초대"""
    from .models import Group, GroupMember, GroupLeaderLog, Notification
    from django.utils import timezone
    group = get_object_or_404(Group, pk=pk)
    my_membership = GroupMember.objects.filter(
        group=group, user=request.user, is_active=True
    ).first()
    if not my_membership or my_membership.role not in ('leader', 'moderator'):
        messages.error(request, '방장/운영진만 초대할 수 있어요.')
        return redirect('group_detail', pk=pk)

    q = request.GET.get('q', '').strip()
    current_member_ids = set(GroupMember.objects.filter(
        group=group, is_active=True
    ).values_list('user_id', flat=True))
    all_users = CustomUser.objects.filter(
        is_verified=True, is_active=True
    ).exclude(pk=request.user.pk).order_by('dong', 'nickname')
    if q:
        all_users = all_users.filter(
            models.Q(nickname__icontains=q) | models.Q(dong__icontains=q)
        )
    search_results = all_users[:50]

    if request.method == 'POST':
        target_id = request.POST.get('user_id')
        target = get_object_or_404(CustomUser, pk=target_id)
        existing = GroupMember.objects.filter(group=group, user=target).first()
        if existing and existing.is_active:
            messages.warning(request, f'{target.nickname or target.username}님은 이미 멤버예요.')
        else:
            # 이미 활성 멤버면 초대 불필요
            existing = GroupMember.objects.filter(group=group, user=target).first()
            if existing and existing.is_active and existing.join_status == 'approved':
                messages.warning(request, f'{target.nickname or target.username}님은 이미 멤버예요.')
                return redirect('group_invite', pk=pk)
            GroupMember.objects.update_or_create(
                group=group, user=target,
                defaults={'join_status': 'invited', 'is_active': False,
                          'role': 'member'}
            )
            GroupLeaderLog.objects.create(
                group=group, actor=request.user, target=target, action='invite'
            )
            Notification.objects.create(
                recipient=target,
                title=f'[{group.name}] 소모임 초대',
                message=f'{request.user.nickname or request.user.username}님이 "{group.name}" 소모임에 초대했어요! 수락하려면 소모임 페이지를 확인하세요.',
                notification_type='community',
            )
            messages.success(request, f'✅ {target.nickname or target.username}님께 초대장을 보냈어요! 상대방이 수락하면 멤버가 돼요.')
            return redirect('group_invite', pk=pk)

    return render(request, 'group_invite.html', {
        'group': group,
        'search_results': search_results,
        'current_member_ids': current_member_ids,
        'q': q,
    })


@login_required
def user_search_api(request):
    """유저 검색 API (소모임 초대용)"""
    from django.http import JsonResponse
    q = request.GET.get('q', '').strip()
    exclude_group = request.GET.get('group_id')
    if len(q) < 1:
        return JsonResponse({'results': []})
    qs = CustomUser.objects.filter(
        is_verified=True
    ).filter(
        models.Q(nickname__icontains=q) | models.Q(username__icontains=q)
    ).exclude(pk=request.user.pk)
    if exclude_group:
        qs = qs.exclude(
            pk__in=GroupMember.objects.filter(
                group_id=exclude_group, is_active=True
            ).values_list('user_id', flat=True)
        )
    results = [
        {'id': u.pk, 'name': u.nickname or u.username,
         'dong': u.dong or '', 'initial': (u.nickname or u.username)[0].upper()}
        for u in qs[:8]
    ]
    return JsonResponse({'results': results})


# ============================================================================
# 봉사활동 CRUD (소모임장 + 관리자만 작성/편집/삭제)
# ============================================================================
@login_required
def volunteer_create(request):
    from .models import Meetup, Group, GroupMember
    # 소모임장이거나 관리자
    is_leader = GroupMember.objects.filter(
        user=request.user, role='leader', is_active=True
    ).exists()
    if not (request.user.is_staff or is_leader):
        messages.error(request, '소모임장 또는 관리자만 봉사활동을 등록할 수 있어요.')
        return redirect('volunteer_calendar')

    my_groups = []
    if request.user.is_staff:
        my_groups = Group.objects.filter(is_active=True)
    else:
        my_groups = Group.objects.filter(
            groupmember__user=request.user,
            groupmember__role='leader',
            groupmember__is_active=True
        )

    if request.method == 'POST':
        title       = request.POST.get('title','').strip()
        description = request.POST.get('description','').strip()
        location    = request.POST.get('location','').strip()
        scheduled_at = request.POST.get('scheduled_at','').strip()
        max_participants = request.POST.get('max_participants') or None
        group_id    = request.POST.get('group_id') or None
        status      = request.POST.get('status','recruiting')

        if not title:
            messages.error(request, '제목을 입력해주세요.')
            return render(request, 'volunteer_form.html', {'my_groups': my_groups})

        from django.utils.dateparse import parse_datetime
        meetup = Meetup.objects.create(
            title=title,
            description=description,
            location=location,
            scheduled_at=parse_datetime(scheduled_at) if scheduled_at else None,
            max_participants=int(max_participants) if max_participants else None,
            group_id=group_id,
            creator=request.user,
            status=status,
        )
        messages.success(request, f'"{title}" 봉사활동이 등록됐어요!')
        return redirect('volunteer_detail', pk=meetup.pk)

    return render(request, 'volunteer_form.html', {'my_groups': my_groups})


@login_required
def volunteer_edit(request, pk):
    from .models import Meetup, Group, GroupMember
    meetup = get_object_or_404(Meetup, pk=pk)
    is_leader = meetup.creator == request.user or request.user.is_staff
    if not is_leader:
        messages.error(request, '수정 권한이 없어요.')
        return redirect('volunteer_detail', pk=pk)

    my_groups = Group.objects.filter(is_active=True) if request.user.is_staff else         Group.objects.filter(groupmember__user=request.user, groupmember__role='leader', groupmember__is_active=True)

    if request.method == 'POST':
        from django.utils.dateparse import parse_datetime
        meetup.title       = request.POST.get('title', meetup.title).strip()
        meetup.description = request.POST.get('description', meetup.description).strip()
        meetup.location    = request.POST.get('location', meetup.location).strip()
        scheduled_at       = request.POST.get('scheduled_at','').strip()
        if scheduled_at:
            meetup.scheduled_at = parse_datetime(scheduled_at)
        max_p = request.POST.get('max_participants') or None
        meetup.max_participants = int(max_p) if max_p else None
        meetup.status      = request.POST.get('status', meetup.status)
        group_id           = request.POST.get('group_id') or None
        meetup.group_id    = group_id
        meetup.save()
        messages.success(request, '봉사활동이 수정됐어요.')
        return redirect('volunteer_detail', pk=pk)

    return render(request, 'volunteer_form.html', {
        'meetup': meetup,
        'my_groups': my_groups,
        'edit': True,
    })


@login_required
def volunteer_delete(request, pk):
    from .models import Meetup
    meetup = get_object_or_404(Meetup, pk=pk)
    if meetup.creator != request.user and not request.user.is_staff:
        messages.error(request, '삭제 권한이 없어요.')
        return redirect('volunteer_detail', pk=pk)
    if request.method == 'POST':
        meetup.delete()
        messages.success(request, '봉사활동이 삭제됐어요.')
        return redirect('volunteer_calendar')
    return redirect('volunteer_detail', pk=pk)


# ============================================================================
# 봉사활동 - 관리자 승인 / 완료 처리 / 평가
# ============================================================================
@login_required
def volunteer_confirm(request, pk):
    """관리자 승인 → 모집중으로 변경 + 전체 알림"""
    from .models import Meetup, Notification
    if not request.user.is_staff:
        messages.error(request, '관리자만 승인할 수 있어요.')
        return redirect('volunteer_detail', pk=pk)
    meetup = get_object_or_404(Meetup, pk=pk)
    if request.method == 'POST':
        from django.utils import timezone
        meetup.is_confirmed = True
        meetup.status = 'recruiting'
        meetup.confirmed_by = request.user
        meetup.confirmed_at = timezone.now()
        meetup.save()
        # 전체 알림 발송
        from .models import CustomUser
        users = CustomUser.objects.filter(is_active=True).exclude(pk=meetup.creator.pk)
        notifications = [
            Notification(
                recipient=u,
                title=f'새 봉사활동 모집: {meetup.title}',
                message=f'{meetup.scheduled_at.strftime("%m/%d") if meetup.scheduled_at else ""} | {meetup.location} | 최대 {meetup.max_participants}명',
                notification_type='activity',
                link=f'/volunteer/{meetup.pk}/',
            ) for u in users
        ]
        Notification.objects.bulk_create(notifications, ignore_conflicts=True)
        messages.success(request, f'"{meetup.title}" 승인 완료! {len(notifications)}명에게 알림을 보냈어요.')

        # 전체채팅에 공지 메시지 발송
        from .models import PublicChat
        PublicChat.objects.create(
            author=request.user,
            message=(
                f"📢 [봉사활동 모집 공고]\n"
                f"\n"
                f"🤝 {meetup.title}\n"
                f"📅 {meetup.scheduled_at.strftime('%m월 %d일 %H:%M') if meetup.scheduled_at else '일정 미정'}\n"
                f"📍 {meetup.location or '장소 미정'}\n"
                f"👥 최대 {meetup.max_participants or '제한없음'}명 모집\n"
                f"\n"
                f"👉 자세히 보기: /volunteer/{meetup.pk}/"
            ),
            is_pinned=True,
        )
    return redirect('volunteer_detail', pk=pk)


@login_required
def volunteer_complete(request, pk):
    """활동 완료 처리"""
    from .models import Meetup
    meetup = get_object_or_404(Meetup, pk=pk)
    if meetup.creator != request.user and not request.user.is_staff:
        messages.error(request, '권한이 없어요.')
        return redirect('volunteer_detail', pk=pk)
    if request.method == 'POST':
        meetup.status = 'completed'
        meetup.result_note = request.POST.get('result_note', '').strip()
        meetup.save()
        messages.success(request, '활동이 완료 처리됐어요. 참가자들이 평가를 남길 수 있어요.')
    return redirect('volunteer_detail', pk=pk)


@login_required
def volunteer_rate(request, pk):
    """봉사활동 평가 (참가자만)"""
    from .models import Meetup, MeetupRating
    meetup = get_object_or_404(Meetup, pk=pk)

    if meetup.status != 'completed':
        messages.error(request, '완료된 활동만 평가할 수 있어요.')
        return redirect('volunteer_detail', pk=pk)

    if not meetup.participants.filter(pk=request.user.pk).exists():
        messages.error(request, '참가자만 평가할 수 있어요.')
        return redirect('volunteer_detail', pk=pk)

    if MeetupRating.objects.filter(meetup=meetup, rater=request.user).exists():
        messages.warning(request, '이미 평가를 남기셨어요.')
        return redirect('volunteer_detail', pk=pk)

    if request.method == 'POST':
        score   = int(request.POST.get('score', 3))
        comment = request.POST.get('comment', '').strip()
        MeetupRating.objects.create(meetup=meetup, rater=request.user, score=score, comment=comment)

        # 평균 평점 업데이트
        ratings = MeetupRating.objects.filter(meetup=meetup)
        meetup.avg_rating   = sum(r.score for r in ratings) / len(ratings)
        meetup.rating_count = len(ratings)
        meetup.save(update_fields=['avg_rating', 'rating_count'])

        # 평가자에게 포인트 지급
        request.user.mileage_points = (request.user.mileage_points or 0) + 5
        request.user.save(update_fields=['mileage_points'])

        messages.success(request, f'평가 완료! 포인트 5점이 적립됐어요.')
        return redirect('volunteer_detail', pk=pk)

    return render(request, 'volunteer_rate.html', {'meetup': meetup})

# ============================================================================
# 허브 페이지
# ============================================================================
def hub_together(request):
    """함께하기 허브"""
    from .models import Group, Meetup, Survey, Post, Board, ActivityProof
    from django.utils import timezone

    groups = Group.objects.filter(is_active=True).order_by('-created_at')[:4]
    meetups = Meetup.objects.filter(
        status__in=['recruiting','confirmed','planned']
    ).order_by('scheduled_at')[:3]
    surveys = Survey.objects.order_by('-created_at')[:3]
    activity_proofs = ActivityProof.objects.filter(status='approved').order_by('-approved_at')[:3]
    # 나눔/장터 게시판 게시글 (board_type=trade 또는 id=14)
    trade_board = None
    trade_posts = []
    try:
        trade_board = Board.objects.filter(board_type='trade', is_active=True).first() or \
                      Board.objects.filter(id=14, is_active=True).first()
        if trade_board:
            trade_posts = Post.objects.filter(board=trade_board, is_active=True).order_by('-created_at')[:4]
    except: pass
    return render(request, 'hub_together.html', {
        'groups': groups,
        'meetups': meetups,
        'surveys': surveys,
        'activity_proofs': activity_proofs,
        'trade_posts': trade_posts,
        'trade_board': trade_board,
    })

def hub_news(request):
    """단지소식 허브"""
    from .models import Post, Board, ManagementDocument, Group, Meetup

    notices = Post.objects.filter(is_active=True, board__board_type='notice').order_by('-created_at')[:4]
    faq_posts = Post.objects.filter(is_active=True, board__board_type='faq').order_by('-created_at')[:4]
    docs = ManagementDocument.objects.order_by('-created_at')[:4]

    # 민원/오류
    complaints = Post.objects.filter(is_active=True, board__board_type='complaint').order_by('-created_at')[:3]

    # 단지통계
    stats_data = {}
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        stats_data = {
            'total_users': User.objects.count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
            'total_groups': Group.objects.filter(is_active=True).count(),
            'total_meetups': Meetup.objects.filter(status='completed').count(),
        }
    except: pass

    return render(request, 'hub_news.html', {
        'notices': notices,
        'complaints': complaints,
        'stats_data': stats_data,
        'docs': docs,
        'faq_posts': faq_posts,
    })

# ── FAQ 지식베이스 ──────────────────────────────────────────
def faq_view(request):
    """노션 스타일 FAQ 지식베이스 - 2단계 대분류/소분류"""
    from .models import Board, Post
    from django.db.models import Q
    from collections import defaultdict, OrderedDict

    faq_board = Board.objects.filter(board_type='qna', is_active=True).first() or \
                Board.objects.filter(id=13, is_active=True).first()

    q        = request.GET.get('q', '').strip()
    major    = request.GET.get('major', '').strip()   # 대분류
    minor    = request.GET.get('minor', '').strip()   # 소분류
    show_all = request.GET.get('show', '') == 'all'

    all_posts = Post.objects.filter(
        board=faq_board, is_active=True
    ).order_by('-is_pinned', '-view_count', '-created_at') if faq_board else Post.objects.none()

    # 검색
    if q:
        all_posts = all_posts.filter(
            Q(title__icontains=q) | Q(content__icontains=q) | Q(tag__icontains=q)
        )
    # 소분류 필터
    if minor:
        all_posts = all_posts.filter(tag=minor)
    # 대분류 필터 (소분류 없을 때)
    elif major:
        all_posts = all_posts.filter(tag__startswith=major + '>')

    # 2단계 카테고리 구조 파싱
    # allowed_tags 형식: "대분류>소분류,대분류>소분류2,..."
    cat_tree = OrderedDict()  # {대분류: [소분류, ...]}
    if faq_board:
        for tag in faq_board.get_tags_list():
            if '>' in tag:
                maj, min_ = tag.split('>', 1)
                if maj not in cat_tree:
                    cat_tree[maj] = []
                cat_tree[maj].append(min_.strip())
            else:
                if tag not in cat_tree:
                    cat_tree[tag] = []

    # 대분류별 게시물 수
    cat_counts = defaultdict(int)
    total_posts = Post.objects.filter(board=faq_board, is_active=True) if faq_board else Post.objects.none()
    for post in total_posts:
        if post.tag and '>' in post.tag:
            maj = post.tag.split('>')[0]
            cat_counts[maj] += 1
        elif post.tag:
            cat_counts[post.tag] += 1

    # 인기 질문 TOP 5
    popular = list(total_posts.order_by('-view_count')[:5]) if faq_board else []

    # 답변 미등록 (PENDING) 목록 - 관리자용
    pending_posts = []
    if faq_board and hasattr(request, 'user') and request.user.is_staff:
        pending_posts = total_posts.filter(content__contains='조만간 답변 예정').order_by('tag')

    # 3단계 점진적 로딩
    # 1단계: 기본 - 인기 TOP 10만 표시
    # 2단계: 대분류 선택 - 해당 대분류 인기 10개
    # 3단계: 소분류 선택 - 해당 소분류 전체

    stage = 1
    display_posts = Post.objects.none()

    if q:
        # 검색: 전체 검색 결과
        stage = 0
        display_posts = all_posts
    elif minor:
        # 3단계: 소분류 전체
        stage = 3
        display_posts = all_posts
    elif major:
        # 2단계: 대분류 인기 10개
        stage = 2
        display_posts = all_posts.order_by('-view_count', '-created_at')[:10]
    else:
        # 1단계: 전체 인기 TOP 10
        stage = 1
        display_posts = total_posts.order_by('-view_count', '-created_at')[:10]

    return render(request, 'faq/faq_main.html', {
        'faq_board':     faq_board,
        'posts':         display_posts,
        'popular':       popular,
        'cat_tree':      cat_tree,
        'cat_counts':    dict(cat_counts),
        'q':             q,
        'major':         major,
        'minor':         minor,
        'show_all':      show_all,
        'stage':         stage,
        'total':         all_posts.count(),
        'pending_posts': pending_posts,
        'total_all':     total_posts.count(),
    })


def faq_upload_csv(request):
    """FAQ CSV 일괄 업로드 (관리자 전용)"""
    from .models import Board, Post
    import csv, io

    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    faq_board = Board.objects.filter(board_type='qna', is_active=True).first() or \
                Board.objects.filter(id=13, is_active=True).first()

    result = {'success': 0, 'error': 0, 'errors': []}

    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if csv_file:
            try:
                decoded = csv_file.read().decode('utf-8-sig')
                reader = csv.DictReader(io.StringIO(decoded))
                for i, row in enumerate(reader, 1):
                    try:
                        title = row.get('질문', row.get('question', '')).strip()
                        content = row.get('답변', row.get('answer', '')).strip()
                        tag = row.get('카테고리', row.get('category', '')).strip()
                        if not title or not content:
                            result['errors'].append(f"행 {i}: 질문 또는 답변 없음")
                            result['error'] += 1
                            continue
                        Post.objects.create(
                            board=faq_board,
                            author=request.user,
                            title=title,
                            content=content,
                            tag=tag,
                            is_active=True,
                        )
                        result['success'] += 1
                    except Exception as e:
                        result['errors'].append(f"행 {i}: {str(e)}")
                        result['error'] += 1
            except Exception as e:
                result['errors'].append(f"파일 오류: {str(e)}")

        from django.contrib import messages
        if result['success']:
            messages.success(request, f"✅ {result['success']}개 FAQ 등록 완료!")
        if result['error']:
            messages.warning(request, f"⚠️ {result['error']}개 오류 발생")
        return render(request, 'faq/faq_upload.html', {
            'result': result, 'faq_board': faq_board
        })

    return render(request, 'faq/faq_upload.html', {'faq_board': faq_board})

def faq_sample_csv(request):
    """FAQ 샘플 CSV 다운로드"""
    import csv
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="faq_sample.csv"'
    writer = csv.writer(response)
    writer.writerow(['질문', '답변', '카테고리'])
    samples = [
        ('관리비는 언제 납부하나요?', '매월 25일까지 납부해주세요. 앱에서 납부하거나 자동이체 신청도 가능합니다.', '관리비'),
        ('관리비 자동이체는 어떻게 신청하나요?', '관리사무소에 방문하거나 앱에서 신청 가능합니다. 은행 계좌번호와 신분증이 필요합니다.', '관리비'),
        ('주차 등록은 어떻게 하나요?', '관리사무소에 차량등록증을 지참하여 방문해주세요. 세대당 1대 기본 등록이 무료입니다.', '주차'),
        ('방문 차량 주차는 어떻게 하나요?', '경비실에서 방문증을 수령하시면 지정 구역에 주차 가능합니다. 최대 2시간 무료입니다.', '주차'),
        ('택배 보관은 어떻게 되나요?', '경비실에서 대리 수령 후 3일간 보관합니다. 스마트 택배함도 이용 가능합니다.', '택배/배달'),
        ('층간소음 발생 시 어떻게 해야 하나요?', '먼저 관리사무소에 신고해주세요. 공동생활 에티켓 안내 후에도 지속될 경우 층간소음 위원회에 조정을 신청할 수 있습니다.', '생활규칙'),
        ('분리수거는 언제 하나요?', '월/수/금 저녁 6시~9시에 분리수거장에 배출해주세요. 대형폐기물은 스티커 구입 후 별도 배출합니다.', '분리수거'),
        ('헬스장 이용 시간은 언제인가요?', '오전 6시~오후 10시까지 이용 가능합니다. 앱에서 예약 후 이용하시면 됩니다.', '시설이용'),
        ('입주민 인증은 어떻게 하나요?', '앱에서 동/호수와 관리비 고지서를 첨부하여 신청하시면 24시간 내에 승인됩니다.', '앱사용법'),
        ('비밀번호를 잊었어요', '로그인 화면에서 비밀번호 찾기를 클릭하신 후 가입 시 등록한 이메일로 재설정 링크를 받으실 수 있습니다.', '앱사용법'),
    ]
    for row in samples:
        writer.writerow(row)
    return response




# ── 이웃 온기 점수
from django.db.models import Avg as _Avg

@login_required
def rating_list(request):
    from .models import Rating
    ratings_received = Rating.objects.filter(rated_user=request.user).select_related('rater').order_by('-created_at')
    ratings_given = Rating.objects.filter(rater=request.user).select_related('rated_user').order_by('-created_at')
    avg_score = ratings_received.aggregate(avg=_Avg('score'))['avg'] or 0
    return render(request, 'core/rating_list.html', {
        'ratings_received': ratings_received,
        'ratings_given': ratings_given,
        'avg_score': round(avg_score, 1),
        'manners_score': request.user.manners_score,
    })


@login_required
def rating_give(request, user_pk):
    from .models import Rating
    from django.contrib.auth import get_user_model
    target_user = get_object_or_404(get_user_model(), pk=user_pk)
    if target_user == request.user:
        messages.error(request, '자신에게 평가할 수 없습니다.')
        return redirect('rating_list')
    existing = Rating.objects.filter(rater=request.user, rated_user=target_user).first()
    if request.method == 'POST':
        score = int(request.POST.get('score', 5))
        comment = request.POST.get('comment', '').strip()
        if existing:
            existing.score = score
            existing.comment = comment
            existing.save()
        else:
            Rating.objects.create(rater=request.user, rated_user=target_user, score=score, comment=comment)
        avg = Rating.objects.filter(rated_user=target_user).aggregate(avg=_Avg('score'))['avg'] or 5
        target_user.manners_score = round(avg * 20, 1)
        target_user.save(update_fields=['manners_score'])
        messages.success(request, '평가가 저장되었습니다. 💚')
        return redirect('rating_list')
    return render(request, 'core/rating_give.html', {
        'target_user': target_user,
        'existing': existing,
        'score_range': range(1, 6),
    })


# ── 설문조사 (공통: 게시판 + 소모임)
@login_required
def poll_create(request):
    from .models import Poll
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)
    import json
    data = json.loads(request.body)
    question = data.get('question', '').strip()
    options  = data.get('options', [])
    post_id  = data.get('post_id')
    group_id = data.get('group_id')
    if not question or len(options) < 2:
        return JsonResponse({'error': '질문과 옵션 2개 이상 필요'}, status=400)
    votes = {str(i): 0 for i in range(len(options))}
    kwargs = {'question': question, 'options': options, 'votes': votes}
    if post_id:
        from .models import Post as _Post
        kwargs['post'] = get_object_or_404(_Post, pk=post_id)
    if group_id:
        from .models import Group as _Group
        kwargs['group'] = get_object_or_404(_Group, pk=group_id)
    poll = Poll.objects.create(**kwargs)
    return JsonResponse({'success': True, 'poll_id': poll.id})


@login_required
def poll_vote(request, poll_id):
    from .models import Poll
    poll = get_object_or_404(Poll, pk=poll_id, is_active=True)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)
    import json
    data = json.loads(request.body)
    idx  = str(data.get('option_index'))
    if idx not in poll.votes:
        return JsonResponse({'error': '잘못된 옵션'}, status=400)
    poll.votes[idx] = poll.votes.get(idx, 0) + 1
    poll.save(update_fields=['votes'])
    total = sum(poll.votes.values())
    result = []
    for i, opt in enumerate(poll.options):
        cnt = poll.votes.get(str(i), 0)
        result.append({'text': opt, 'count': cnt, 'pct': round(cnt/total*100) if total else 0})
    return JsonResponse({'success': True, 'results': result, 'total': total})


def poll_results(request, poll_id):
    from .models import Poll
    poll = get_object_or_404(Poll, pk=poll_id)
    total = sum(poll.votes.values()) if poll.votes else 0
    result = []
    for i, opt in enumerate(poll.options):
        cnt = poll.votes.get(str(i), 0)
        result.append({'text': opt, 'count': cnt, 'pct': round(cnt/total*100) if total else 0})
    return JsonResponse({'question': poll.question, 'results': result, 'total': total})


@login_required
def group_post_edit(request, pk, post_pk):
    from .models import Group, GroupPost, GroupMember
    group = get_object_or_404(Group, pk=pk)
    post = get_object_or_404(GroupPost, pk=post_pk, group=group)
    if post.author != request.user and not request.user.is_staff:
        messages.error(request, "수정 권한이 없습니다.")
        return redirect("group_post_detail", pk=pk, post_pk=post_pk)
    if request.method == "POST":
        post.title = request.POST.get("title", post.title).strip()
        post.content = request.POST.get("content", post.content).strip()
        post.save()
        messages.success(request, "글이 수정되었습니다.")
        return redirect("group_post_detail", pk=pk, post_pk=post_pk)
    return render(request, "groups/group_post_form.html", {"group": group, "post": post})
