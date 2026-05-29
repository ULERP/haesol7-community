from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Letter, CustomUser


@login_required
def letter_inbox(request):
    letters = Letter.objects.filter(receiver=request.user, receiver_deleted=False).select_related("sender")
    unread_count = letters.filter(is_read=False).count()
    return render(request, "letters/inbox.html", {"letters": letters, "unread_count": unread_count, "tab": "inbox"})


@login_required
def letter_sent(request):
    letters = Letter.objects.filter(sender=request.user, sender_deleted=False).select_related("receiver")
    return render(request, "letters/sent.html", {"letters": letters, "tab": "sent"})


@login_required
def letter_detail(request, pk):
    letter = get_object_or_404(Letter, pk=pk)
    if letter.receiver != request.user and letter.sender != request.user:
        messages.error(request, "접근 권한이 없습니다.")
        return redirect("letter_inbox")
    if letter.receiver == request.user and not letter.is_read:
        letter.is_read = True
        letter.save(update_fields=["is_read"])
    return render(request, "letters/detail.html", {"letter": letter})


@login_required
def letter_write(request, receiver_id=None):
    receiver = None
    if receiver_id:
        receiver = get_object_or_404(CustomUser, pk=receiver_id)
    if request.method == "POST":
        receiver_pk = request.POST.get("receiver_id")
        subject = request.POST.get("subject", "").strip()
        content = request.POST.get("content", "").strip()
        parent_id = request.POST.get("parent_id")
        try:
            recv_user = CustomUser.objects.get(pk=receiver_pk)
        except CustomUser.DoesNotExist:
            messages.error(request, "받는 사람을 찾을 수 없습니다.")
            return redirect("letter_inbox")
        if not subject or not content:
            messages.error(request, "제목과 내용을 모두 입력해주세요.")
        else:
            parent = None
            if parent_id:
                try:
                    parent = Letter.objects.get(pk=parent_id)
                except Letter.DoesNotExist:
                    pass
            Letter.objects.create(sender=request.user, receiver=recv_user, subject=subject, content=content, parent=parent)
            messages.success(request, f"{recv_user.nickname}님께 쪽지를 보냈습니다.")
            return redirect("letter_sent")
    users = CustomUser.objects.exclude(pk=request.user.pk).order_by("nickname")
    return render(request, "letters/write.html", {"receiver": receiver, "users": users})


@login_required
def letter_reply(request, pk):
    original = get_object_or_404(Letter, pk=pk, receiver=request.user)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Letter.objects.create(
                sender=request.user, receiver=original.sender,
                subject=f"Re: {original.subject}", content=content, parent=original
            )
            messages.success(request, "답장을 보냈습니다.")
            return redirect("letter_inbox")
    return render(request, "letters/reply.html", {"original": original})


@login_required
def letter_delete(request, pk):
    letter = get_object_or_404(Letter, pk=pk)
    if letter.sender == request.user:
        letter.sender_deleted = True
        letter.save(update_fields=["sender_deleted"])
    elif letter.receiver == request.user:
        letter.receiver_deleted = True
        letter.save(update_fields=["receiver_deleted"])
    if letter.sender_deleted and letter.receiver_deleted:
        letter.delete()
    messages.success(request, "쪽지를 삭제했습니다.")
    return redirect(request.META.get("HTTP_REFERER", "letter_inbox"))
