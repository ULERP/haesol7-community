from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import CustomUser


@login_required
def verify_request(request):
    """입주민 인증 신청"""
    user = request.user
    if user.is_verified:
        messages.info(request, "이미 인증된 계정입니다.")
        return redirect("mypage")

    if request.method == "POST":
        dong  = request.POST.get("dong", "").strip()
        ho    = request.POST.get("ho", "").strip()
        phone = request.POST.get("phone", "").strip()
        if not dong or not ho or not phone:
            messages.error(request, "동, 호수, 연락처를 모두 입력해주세요.")
        else:
            user.dong         = dong
            user.ho           = ho
            user.phone_number = phone
            user.verified_note = "인증 대기중"
            user.save(update_fields=["dong", "ho", "phone_number", "verified_note"])
            messages.success(request, "인증 신청이 완료됐어요! 관리자 확인 후 승인됩니다.")
            return redirect("mypage")

    return render(request, "verify/request.html", {"user": user})


@user_passes_test(lambda u: u.is_staff)
def verify_admin(request):
    """관리자 인증 관리 페이지"""
    pending  = CustomUser.objects.filter(verified_note="인증 대기중", is_verified=False).order_by("date_joined")
    verified = CustomUser.objects.filter(is_verified=True).order_by("-verified_at")
    return render(request, "verify/admin.html", {"pending": pending, "verified": verified})


@user_passes_test(lambda u: u.is_staff)
def verify_approve(request, user_id):
    """인증 승인"""
    target = get_object_or_404(CustomUser, pk=user_id)
    target.is_verified  = True
    target.verified_at  = timezone.now()
    target.verified_note = request.POST.get("note", "관리자 승인")
    target.save(update_fields=["is_verified", "verified_at", "verified_note"])
    messages.success(request, f"{target.nickname}({target.dong}동 {target.ho}호) 인증 승인 완료")
    return redirect("verify_admin")


@user_passes_test(lambda u: u.is_staff)
def verify_reject(request, user_id):
    """인증 거절"""
    target = get_object_or_404(CustomUser, pk=user_id)
    reason = request.POST.get("reason", "인증 거절")
    target.dong         = ""
    target.ho           = ""
    target.verified_note = f"거절: {reason}"
    target.save(update_fields=["dong", "ho", "verified_note"])
    messages.warning(request, f"{target.nickname} 인증 거절 처리됨")
    return redirect("verify_admin")
