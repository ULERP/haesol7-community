"""
해솔7 지킴이 커스텀 AdminSite
- 대시보드 통계 주입
- 승인 대기 알림
"""
from django.contrib.admin import AdminSite
from django.urls import path
from django.shortcuts import render


class HaesolAdminSite(AdminSite):
    site_header = '🌿 해솔7 지킴이 관리자'
    site_title  = '해솔7 관리자'
    index_title = '관리 대시보드'

    def get_app_list(self, request, app_label=None):
        """앱 목록 반환 (기본 동작 유지)"""
        return super().get_app_list(request, app_label)

    def index(self, request, extra_context=None):
        """대시보드 - 통계 및 승인 대기 주입"""
        from .models import (
            CustomUser, Post, Group, ActivityProof,
            Survey, Notification, CalendarEvent, Meetup
        )
        from django.utils import timezone
        from datetime import timedelta

        now   = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)

        extra_context = extra_context or {}
        extra_context.update({
            # 현황 통계
            'stat_total_users':       CustomUser.objects.filter(is_active=True).count(),
            'stat_unverified':        CustomUser.objects.filter(is_verified=False, is_active=True).count(),
            'stat_new_users_week':    CustomUser.objects.filter(date_joined__gte=week_ago).count(),
            'stat_total_posts':       Post.objects.filter(is_active=True).count(),
            'stat_pending_proofs':    ActivityProof.objects.filter(status='pending').count(),
            'stat_pending_groups':    Group.objects.filter(status='pending').count(),
            'stat_pending_calendar':  CalendarEvent.objects.filter(visibility__in=['pending','group_pending']).count(),
            'stat_pending_meetups':   Meetup.objects.filter(is_confirmed=False, status='planned').count(),
            'stat_active_surveys':    Survey.objects.filter(status='active').count(),
            'stat_unread_noti':       Notification.objects.filter(is_read=False).count(),
            # 최근 가입자
            'recent_users': CustomUser.objects.filter(
                is_active=True
            ).order_by('-date_joined')[:5],
            # 승인 대기 목록 (최근 5건씩)
            'pending_proofs': ActivityProof.objects.filter(
                status='pending'
            ).select_related('user','activity').order_by('-submitted_at')[:5],
            'pending_groups': Group.objects.filter(
                status='pending'
            ).select_related('creator').order_by('-created_at')[:5],
            'pending_calendar': CalendarEvent.objects.filter(
                visibility__in=['pending','group_pending']
            ).select_related('creator','group').order_by('-created_at')[:5],
        })
        return super().index(request, extra_context)


# 싱글톤 인스턴스
haesol_admin = HaesolAdminSite(name='haesol_admin')
