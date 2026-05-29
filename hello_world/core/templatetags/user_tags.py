from django import template
register = template.Library()

@register.filter
def display_name(user):
    """닉네임 or 아이디 표시"""
    if not user:
        return '알 수 없음'
    name = user.nickname or user.username
    if user.unit_number:
        return f"{name} ({user.unit_number})"
    return name

@register.filter
def display_name_short(user):
    """닉네임 or 아이디만 (동호수 없이)"""
    if not user:
        return '알 수 없음'
    return user.nickname or user.username
