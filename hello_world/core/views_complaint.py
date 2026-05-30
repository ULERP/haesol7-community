from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db import models as m
from .models import Complaint, Notice, ComplaintCategory, NoticeCategory


@login_required
def complaint_list(request):
    my = Complaint.objects.filter(author=request.user).select_related("category")
    return render(request, "complaint/list.html", {"complaints": my})


@login_required
def complaint_create(request):
    categories = ComplaintCategory.objects.filter(is_active=True)
    if request.method == "POST":
        title    = request.POST.get("title", "").strip()
        content  = request.POST.get("content", "").strip()
        cat_id   = request.POST.get("category")
        is_anon  = request.POST.get("is_anonymous") == "on"
        if not title or not content:
            messages.error(request, "제목과 내용을 입력해주세요.")
        else:
            cat = ComplaintCategory.objects.filter(pk=cat_id).first()
            Complaint.objects.create(
                author=request.user, title=title, content=content,
                category=cat, is_anonymous=is_anon
            )
            messages.success(request, "민원/건의가 접수됐어요! 관리자 검토 후 답변드립니다.")
            return redirect("complaint_list")
    return render(request, "complaint/form.html", {"categories": categories})


@login_required
def complaint_detail(request, pk):
    c = get_object_or_404(Complaint, pk=pk)
    if c.author != request.user and not request.user.is_staff:
        messages.error(request, "접근 권한이 없습니다.")
        return redirect("complaint_list")
    return render(request, "complaint/detail.html", {"c": c})


@user_passes_test(lambda u: u.is_staff)
def complaint_admin(request):
    qs = Complaint.objects.select_related("author", "category").all()
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)
    return render(request, "complaint/admin.html", {"complaints": qs, "status": status})


@user_passes_test(lambda u: u.is_staff)
def complaint_reply(request, pk):
    c = get_object_or_404(Complaint, pk=pk)
    if request.method == "POST":
        c.admin_reply = request.POST.get("reply", "").strip()
        c.status      = request.POST.get("status", "done")
        c.replied_at  = timezone.now()
        c.save(update_fields=["admin_reply", "status", "replied_at"])
        messages.success(request, "답변이 등록됐어요.")
    return redirect("complaint_admin")


def notice_list(request):
    notices = Notice.objects.select_related("notice_type", "author").filter(
        m.Q(expires_at__isnull=True) | m.Q(expires_at__gte=timezone.now())
    )
    return render(request, "notice/list.html", {"notices": notices})


@user_passes_test(lambda u: u.is_staff)
def notice_create(request):
    types = NoticeCategory.objects.filter(is_active=True)
    if request.method == "POST":
        ntype = NoticeCategory.objects.filter(pk=request.POST.get("notice_type")).first()
        Notice.objects.create(
            author      = request.user,
            notice_type = ntype,
            title       = request.POST.get("title", "").strip(),
            content     = request.POST.get("content", "").strip(),
            is_pinned   = request.POST.get("is_pinned") == "on",
        )
        messages.success(request, "공지가 등록됐어요.")
        return redirect("notice_list")
    return render(request, "notice/form.html", {"types": types})


@user_passes_test(lambda u: u.is_staff)
def notice_delete(request, pk):
    n = get_object_or_404(Notice, pk=pk)
    n.delete()
    messages.success(request, "공지를 삭제했어요.")
    return redirect("notice_list")
