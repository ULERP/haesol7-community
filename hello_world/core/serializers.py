from rest_framework import serializers
from django.contrib.auth import get_user_model
from hello_world.core.models import (
    Badge, Activity, ActivityProof, UserBadge, Rating,
    Notification, ChatHistory, ManagementDocument,
    Group, GroupMember, Meetup, GroupPost, GroupComment, GroupChat,
    Category, Post
)
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

User = get_user_model()

# ============================================================================
# 사용자 관련 Serializers
# ============================================================================

class UserBadgeSerializer(serializers.ModelSerializer):
    badge_title = serializers.CharField(source='badge.title', read_only=True)
    badge_icon = serializers.ImageField(source='badge.icon', read_only=True)
    
    class Meta:
        model = UserBadge
        fields = ('id', 'badge', 'badge_title', 'badge_icon', 'earned_at', 'is_displayed')


class UserProfileSerializer(serializers.ModelSerializer):
    """사용자 프로필 - 마일리지, 배지, 온기점수 포함"""
    user_badges = UserBadgeSerializer(many=True, read_only=True)
    activity_count = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'unit_number', 'phone_number', 'profile_image', 'introduction',
            'mileage_points', 'manners_score', 'user_badges',
            'activity_count', 'total_points', 'created_at'
        )
        read_only_fields = ('mileage_points', 'manners_score', 'user_badges')
    
    def get_activity_count(self, obj):
        return ActivityProof.objects.filter(user=obj, status='approved').count()
    
    def get_total_points(self, obj):
        return obj.mileage_points


class SimpleUserSerializer(serializers.ModelSerializer):
    """간단한 사용자 정보"""
    class Meta:
        model = User
        fields = ('id', 'username', 'profile_image', 'manners_score')


# ============================================================================
# 마일리지 & 배지 Serializers
# ============================================================================

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ('id', 'title', 'description', 'icon', 'category', 'required_points', 'required_activities')


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ('id', 'name', 'activity_type', 'description', 'base_points', 'points_per_hour', 'is_active')


class ActivityProofSerializer(serializers.ModelSerializer):
    activity_name = serializers.CharField(source='activity.name', read_only=True)
    activity_type = serializers.CharField(source='activity.activity_type', read_only=True)
    
    class Meta:
        model = ActivityProof
        fields = (
            'id', 'activity', 'activity_name', 'activity_type',
            'title', 'description', 'proof_image', 'duration_hours',
            'status', 'points_earned', 'submitted_at', 'approved_at'
        )
        read_only_fields = ('status', 'points_earned', 'submitted_at', 'approved_at')


class ActivityProofCreateSerializer(serializers.ModelSerializer):
    """활동 인증 제출용 Serializer"""
    class Meta:
        model = ActivityProof
        fields = ('activity', 'title', 'description', 'proof_image', 'duration_hours')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='name',
        allow_null=True,
        required=False
    )

    class Meta:
        model = Post
        fields = (
            'id', 'board', 'category', 'author', 'author_username',
            'title', 'content', 'tag', 'is_pinned', 'is_anonymous',
            'view_count', 'like_count', 'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = ('author', 'view_count', 'like_count', 'created_at', 'updated_at')


# ============================================================================
# 이웃 온기 (Rating) Serializers
# ============================================================================

class RatingSerializer(serializers.ModelSerializer):
    rater_username = serializers.CharField(source='rater.username', read_only=True)
    
    class Meta:
        model = Rating
        fields = ('id', 'rater', 'rater_username', 'rated_user', 'score', 'comment', 'category', 'created_at')
        read_only_fields = ('created_at',)


# ============================================================================
# LLM 에이전트 Serializers
# ============================================================================

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'id', 'title', 'message', 'notification_type', 'persona',
            'is_read', 'is_sent', 'created_at', 'read_at'
        )
        read_only_fields = ('created_at', 'read_at')


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = (
            'id', 'question', 'answer', 'referenced_documents',
            'confidence_score', 'is_helpful', 'created_at'
        )
        read_only_fields = ('answer', 'confidence_score', 'created_at')


class ManagementDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagementDocument
        fields = ('id', 'title', 'content', 'category', 'is_active')


# ============================================================================
# 소그룹 & 모임 Serializers
# ============================================================================

class GroupMemberSerializer(serializers.ModelSerializer):
    user_info = SimpleUserSerializer(source='user', read_only=True)
    
    class Meta:
        model = GroupMember
        fields = ('id', 'user', 'user_info', 'role', 'joined_at', 'is_active')


class GroupSerializer(serializers.ModelSerializer):
    creator_info = SimpleUserSerializer(source='creator', read_only=True)
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = (
            'id', 'name', 'description', 'group_type', 'creator',
            'creator_info', 'group_image', 'location', 'regular_schedule',
            'member_limit', 'is_public', 'is_active',
            'member_count', 'is_member', 'created_at'
        )
        read_only_fields = ('created_at', 'creator')
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.members.filter(id=request.user.id).exists()
        return False


class GroupDetailSerializer(GroupSerializer):
    members = GroupMemberSerializer(source='groupmember_set', many=True, read_only=True)


class MeetupSerializer(serializers.ModelSerializer):
    creator_info = SimpleUserSerializer(source='creator', read_only=True)
    participant_count = serializers.SerializerMethodField()
    is_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Meetup
        fields = (
            'id', 'group', 'title', 'description', 'creator',
            'creator_info', 'location', 'scheduled_at', 'duration_minutes',
            'max_participants', 'status', 'thumbnail',
            'participant_count', 'is_participant', 'created_at'
        )
        read_only_fields = ('created_at', 'creator')
    
    def get_participant_count(self, obj):
        return obj.participants.count()
    
    def get_is_participant(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.participants.filter(id=request.user.id).exists()
        return False


class GroupCommentSerializer(serializers.ModelSerializer):
    author_info = SimpleUserSerializer(source='author', read_only=True)
    
    class Meta:
        model = GroupComment
        fields = ('id', 'post', 'author', 'author_info', 'content', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class GroupPostSerializer(serializers.ModelSerializer):
    author_info = SimpleUserSerializer(source='author', read_only=True)
    comments = GroupCommentSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupPost
        fields = (
            'id', 'group', 'author', 'author_info', 'title', 'content',
            'image', 'like_count', 'comment_count', 'comments',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at', 'like_count')
    
    def get_comment_count(self, obj):
        return obj.comments.count()


class GroupChatSerializer(serializers.ModelSerializer):
    sender_info = SimpleUserSerializer(source='sender', read_only=True)
    
    class Meta:
        model = GroupChat
        fields = ('id', 'group', 'sender', 'sender_info', 'message', 'image', 'created_at')
        read_only_fields = ('created_at',)
