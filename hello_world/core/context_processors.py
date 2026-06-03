from hello_world.core.models import PublicChat, Post, CustomUser
from django.utils import timezone
from datetime import timedelta

def sidebar_data(request):
    """모든 페이지 우측 패널용 데이터"""
    try:
        recent_chats = PublicChat.objects.filter(
            is_active=True
        ).select_related('author').order_by('-created_at')[:6]
    except:
        recent_chats = []

    try:
        week_ago = timezone.now() - timedelta(days=7)
        hot_posts = Post.objects.filter(
            is_active=True, created_at__gte=week_ago
        ).order_by('-like_count', '-created_at')[:5]
    except:
        hot_posts = []

    try:
        online_users = CustomUser.objects.filter(
            is_active=True, is_verified=True
        ).order_by('-last_login')[:8]
    except:
        online_users = []

    return {
        'sidebar_chats': recent_chats,
        'sidebar_hot_posts': hot_posts,
        'sidebar_online_users': online_users,
    }
