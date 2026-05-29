from django.shortcuts import render, get_object_or_404
from hello_world.core.models import Board, Post, ManagementDocument
def index(request):
    boards = Board.objects.filter(is_active=True).order_by('order')
    recent_posts = Post.objects.filter(is_active=True).order_by('-created_at')[:10]
    return render(request, 'community/index.html', {'boards': boards, 'recent_posts': recent_posts})
def board_detail(request, board_id):
    board = get_object_or_404(Board, pk=board_id, is_active=True)
    posts = Post.objects.filter(board=board, is_active=True)
    return render(request, 'community/board_detail.html', {'board': board, 'posts': posts})
def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id, is_active=True)
    Post.objects.filter(pk=post_id).update(view_count=post.view_count+1)
    return render(request, 'community/post_detail.html', {'post': post})
# =====================================================
# 관리 문서 게시판 (ManagementDocument)
# =====================================================
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy

class ManagementDocumentListView(LoginRequiredMixin, ListView):
    model = ManagementDocument
    template_name = 'community/management_doc_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        qs = ManagementDocument.objects.filter(is_active=True)
        category = self.request.GET.get('category', '')
        q = self.request.GET.get('q', '')
        if category:
            qs = qs.filter(category=category)
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(content__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = ManagementDocument.objects.filter(is_active=True).values_list('category', flat=True).distinct().order_by('category')
        ctx['selected_category'] = self.request.GET.get('category', '')
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class ManagementDocumentDetailView(LoginRequiredMixin, DetailView):
    model = ManagementDocument
    template_name = 'community/management_doc_detail.html'
    context_object_name = 'document'


class ManagementDocumentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ManagementDocument
    template_name = 'community/management_doc_form.html'
    fields = ['title', 'content', 'category']
    success_url = reverse_lazy('management_doc_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class ManagementDocumentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ManagementDocument
    template_name = 'community/management_doc_form.html'
    fields = ['title', 'content', 'category']
    success_url = reverse_lazy('management_doc_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class ManagementDocumentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ManagementDocument
    template_name = 'community/management_doc_confirm_delete.html'
    success_url = reverse_lazy('management_doc_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser