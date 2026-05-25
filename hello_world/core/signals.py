from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Sum, Count
from hello_world.core.models import (
    ActivityProof, CustomUser, UserBadge, Badge, Rating,
    Notification, GroupMember, Meetup, Activity, GroupComment
)

# ============================================================================
# ① 활동 승인 시 마일리지 및 배지 자동 처리
# ============================================================================

@receiver(post_save, sender=ActivityProof)
def process_activity_points(sender, instance, created, update_fields, **kwargs):
    """
    활동이 승인될 때 자동으로:
    1. 사용자 마일리지 포인트 증가
    2. 배지 자동 획득 여부 확인
    3. 알림 발송
    """
    
    # 새로 생성되었거나, 상태가 변경되었을 때만 처리
    if update_fields and 'status' not in update_fields:
        return
    
    # 승인 상태로 변경된 경우만 처리
    if instance.status == 'approved' and instance.points_earned > 0:
        user = instance.user
        
        # 1. 마일리지 포인트 증가
        old_points = user.mileage_points
        user.mileage_points += instance.points_earned
        user.save()
        
        # 2. 배지 획득 여부 확인 및 자동 지급
        check_and_award_badges(user)
        
        # 3. 축하 알림 발송
        Notification.objects.create(
            recipient=user,
            title=f"🎉 활동 승인됨!",
            message=f"'{instance.activity.name}' 활동이 승인되었습니다! +{instance.points_earned}P 적립되었어요.",
            notification_type='activity',
            persona='다정한 이웃',
            related_activity=instance.activity,
        )


def check_and_award_badges(user):
    """
    사용자가 배지 획득 조건을 만족했는지 확인하고 자동 지급
    """
    all_badges = Badge.objects.filter(is_active=True)
    
    # 사용자의 현재 활동 통계
    user_points = user.mileage_points
    user_activities = ActivityProof.objects.filter(
        user=user,
        status='approved'
    ).count()
    
    for badge in all_badges:
        # 이미 획득한 배지는 스킵
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            continue
        
        # 배지 획득 조건 만족 여부 확인
        points_ok = user_points >= badge.required_points
        activities_ok = user_activities >= badge.required_activities
        
        # 둘 다 만족해야 배지 지급
        if points_ok and activities_ok:
            # 배지 지급
            user_badge = UserBadge.objects.create(user=user, badge=badge)
            user.current_badges.add(badge)
            user.save()
            
            # 배지 획득 알림
            Notification.objects.create(
                recipient=user,
                title=f"🏅 새로운 배지 획득!",
                message=f"축하합니다! '{badge.title}' 배지를 획득하셨어요. 이제 프로필에 표시됩니다.",
                notification_type='badge',
                persona='자랑스러운 이웃',
            )


# ============================================================================
# ② 평가(Rating) 후 이웃 온기(Manners Score) 자동 계산
# ============================================================================

@receiver(post_save, sender=Rating)
def update_manners_score(sender, instance, created, **kwargs):
    """
    새로운 평가가 추가되면 사용자의 이웃 온기 점수를 자동 계산 및 업데이트
    """
    if created:
        recalculate_manners_score(instance.rated_user)


@receiver(post_delete, sender=Rating)
def update_manners_score_on_delete(sender, instance, **kwargs):
    """평가 삭제 시에도 점수 재계산"""
    recalculate_manners_score(instance.rated_user)


def recalculate_manners_score(user):
    """
    이웃 온기 점수 계산 로직:
    1. 받은 평가의 평균
    2. 활동 횟수 (정규화)
    3. 댓글 칭찬 수 (정규화)
    가중치: 평가 50%, 활동 30%, 커뮤니티 20%
    """
    
    # 1. 받은 평가 평균 (1-5 → 0-100)
    ratings = Rating.objects.filter(rated_user=user)
    if ratings.exists():
        avg_rating = ratings.aggregate(avg=Sum('score'))['avg'] / len(ratings) if ratings.exists() else 3
        rating_score = (avg_rating / 5.0) * 100
    else:
        rating_score = 50  # 기본값
    
    # 2. 활동 참여도 (최대 100)
    approved_activities = ActivityProof.objects.filter(
        user=user,
        status='approved'
    ).count()
    activity_score = min(approved_activities * 5, 100)
    
    # 3. 커뮤니티 활동 (댓글 수 기반, 최대 100)
    from hello_world.core.models import GroupComment
    comment_count = GroupComment.objects.filter(author=user).count()
    community_score = min(comment_count * 3, 100)
    
    # 최종 점수 계산 (가중치 적용)
    final_score = (rating_score * 0.5) + (activity_score * 0.3) + (community_score * 0.2)
    final_score = min(max(final_score, 0), 100)  # 0-100 범위로 제한
    
    user.manners_score = final_score
    user.save()


# ============================================================================
# ③ 모임(Meetup) 참여 시 자동 처리
# ============================================================================

@receiver(post_save, sender=GroupMember)
def notify_group_join(sender, instance, created, **kwargs):
    """그룹 가입 시 알림 발송"""
    if created:
        Notification.objects.create(
            recipient=instance.user,
            title=f"👋 {instance.group.name}에 가입했습니다!",
            message=f"이제 {instance.group.name} 그룹의 모든 소식을 받을 수 있어요. 함께 즐거운 시간을 보내세요!",
            notification_type='community',
            persona='따뜻한 동네',
        )


# ============================================================================
# ④ 실시간 알림 시스템 시드 데이터
# ============================================================================

def seed_initial_badges():
    """초기 배지 생성"""
    badges_data = [
        {
            'title': '우리 동네 보안관',
            'description': '야간 순찰에 꾸준히 참여한 지킴이',
            'category': 'security',
            'required_points': 500,
            'required_activities': 20,
        },
        {
            'title': '그린 가디언',
            'description': '환경 정비 활동에 앞장선 지킴이',
            'category': 'environment',
            'required_points': 400,
            'required_activities': 15,
        },
        {
            'title': '펫 프렌드',
            'description': '펫 매너 캠페인의 주역',
            'category': 'community',
            'required_points': 300,
            'required_activities': 10,
        },
        {
            'title': '공동체의 별',
            'description': '커뮤니티 활동의 중심',
            'category': 'community',
            'required_points': 600,
            'required_activities': 25,
        },
    ]
    
    for badge_data in badges_data:
        Badge.objects.get_or_create(
            title=badge_data['title'],
            defaults=badge_data
        )


def seed_initial_activities():
    """초기 활동 카테고리 생성"""
    activities_data = [
        {
            'name': '야간 단지 순찰',
            'activity_type': 'patrol',
            'description': '저녁 8시~10시 단지 순찰',
            'base_points': 100,
            'points_per_hour': 50,
        },
        {
            'name': '펫 매너 캠페인',
            'activity_type': 'manner',
            'description': '반려동물 매너 홍보 활동',
            'base_points': 80,
            'points_per_hour': 40,
        },
        {
            'name': '환경 정비 활동',
            'activity_type': 'cleaning',
            'description': '공용 공간 청소 및 정비',
            'base_points': 70,
            'points_per_hour': 35,
        },
        {
            'name': '이웃 돕기',
            'activity_type': 'helping',
            'description': '어려운 이웃 지원 활동',
            'base_points': 120,
            'points_per_hour': 60,
        },
    ]
    
    for activity_data in activities_data:
        Activity.objects.get_or_create(
            name=activity_data['name'],
            defaults=activity_data
        )
