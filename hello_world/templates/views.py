from django.shortcuts import render, redirect
from hello_world.core.models import Post

def post_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        Post.objects.create(title=title, content=content)
        return redirect('index')
    return render(request, 'post_form.html')
