from .models import Board, Notice, CalendarEvent, Post, PublicChat, CustomUser
from django.utils import timezone
from datetime import timedelta
import requests
from django.conf import settings

def sidebar_context(request):
    """모든 페이지 공통 사이드바 컨텍스트"""
    now = timezone.now()

    # 게시판 목록
    try:
        sb_boards = Board.objects.filter(is_active=True).exclude(
            board_type__in=['trade','qna','gallery','faq','complaint']
        ).exclude(
            name__in=['FAQ','나눔/장터','민원/오류','민원·건의']
        ).order_by('order', 'id')
    except:
        sb_boards = []

    # 최근 공지 2개
    try:
        sb_notices = Notice.objects.filter(
            is_pinned=True
        ).order_by('-created_at')[:2]
        if not sb_notices:
            sb_notices = Notice.objects.order_by('-created_at')[:2]
    except:
        sb_notices = []

    # 이번 주 일정 2개
    try:
        week_end = now + timedelta(days=7)
        sb_events = CalendarEvent.objects.filter(
            visibility='public',
            start_time__gte=now,
            start_time__lte=week_end
        ).order_by('start_time')[:2]
    except:
        sb_events = []

    # 인기글 TOP3
    try:
        sb_hot_posts = Post.objects.filter(
            is_active=True,
            created_at__gte=now - timedelta(days=7)
        ).order_by('-like_count')[:3]
    except:
        sb_hot_posts = []

    # 실시간 채팅 최근 3개
    try:
        sb_chats = PublicChat.objects.select_related('author').order_by('-created_at')[:3]
    except:
        sb_chats = []

    # 온라인 유저 (최근 10분)
    try:
        sb_online_users = CustomUser.objects.filter(
            is_active=True,
            last_login__gte=now - timedelta(minutes=10)
        ).order_by('-last_login')[:8]
        sb_online_count = sb_online_users.count()
    except:
        sb_online_users = []
        sb_online_count = 0

    # 날씨 (화성시)
    sb_weather = None
    try:
        api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')
        if api_key:
            r = requests.get(
                'https://api.openweathermap.org/data/2.5/weather',
                params={'q': 'Hwaseong,KR', 'appid': api_key, 'units': 'metric', 'lang': 'kr'},
                timeout=2
            )
            if r.status_code == 200:
                d = r.json()
                sb_weather = {
                    'temp': round(d['main']['temp']),
                    'desc': d['weather'][0]['description'],
                    'icon': d['weather'][0]['main'],
                }
    except:
        pass

    return {
        'sb_boards': sb_boards,
        'sb_notices': sb_notices,
        'sb_events': sb_events,
        'sb_hot_posts': sb_hot_posts,
        'sb_chats': sb_chats,
        'sb_online_users': sb_online_users,
        'sb_online_count': sb_online_count,
        'sb_weather': sb_weather,
    }
