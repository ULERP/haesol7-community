"""사용자 정의 권한"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """소유자만 수정 가능, 다른 사용자는 조회만"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsActivityApprover(permissions.BasePermission):
    """활동 인증을 승인할 수 있는 권한"""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsGroupMember(permissions.BasePermission):
    """그룹 멤버만 접근 가능"""
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'group'):
            return obj.group.members.filter(id=request.user.id).exists()
        return obj.members.filter(id=request.user.id).exists()


class IsGroupLeader(permissions.BasePermission):
    """그룹 리더만 접근 가능"""
    
    def has_object_permission(self, request, view, obj):
        from hello_world.core.models import GroupMember
        
        if hasattr(obj, 'group'):
            group = obj.group
        else:
            group = obj
        
        member = GroupMember.objects.filter(
            group=group,
            user=request.user,
            role__in=['leader', 'moderator']
        ).exists()
        
        return member


class CanRateUser(permissions.BasePermission):
    """다른 사용자를 평가할 수 있는 권한"""
    
    def has_permission(self, request, view):
        # 활동을 함께 한 사용자끼리만 평가 가능
        return bool(request.user and request.user.is_authenticated)
