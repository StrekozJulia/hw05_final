from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .utils import create_page, create_page_not_cached
from posts.forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required

POSTS_ON_PAGE: int = 10


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('group').all()
    page_obj = create_page(posts,
                           request.GET.get('page'),
                           POSTS_ON_PAGE,
                           'index_page')
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = create_page(posts,
                           request.GET.get('page'),
                           POSTS_ON_PAGE,
                           f'group_page_{slug}')
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    is_author = (user == request.user)
    posts = Post.objects.filter(author=user)
    following = False
    page_obj = create_page(posts,
                           request.GET.get('page'),
                           POSTS_ON_PAGE,
                           f'profile_page_{username}')
    following = (request.user.is_authenticated
                 and Follow.objects.filter(user=request.user,
                                           author=user).exists())
    context = {
        'username': user,
        'page_obj': page_obj,
        'following': following,
        'is_author': is_author,
    }
    return render(request, template, context)


def post_detail(request, post_id: int):
    template = 'posts/post_detail.html'
    post = Post.objects.get(pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    context = {
        'form': form,
    }
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user)
    return render(request,
                  'posts/create_post.html',
                  context)


@login_required
def post_edit(request, post_id: int):
    post = Post.objects.get(pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request,
                  'posts/create_post.html',
                  context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.post = post
        form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    page_obj = create_page_not_cached(posts,
                                      request.GET.get('page'),
                                      POSTS_ON_PAGE)
    context = {'page_obj': page_obj, }
    return render(request, 'posts/index.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user and not Follow.objects.filter(user=user,
                                                    author=author).exists():
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if Follow.objects.filter(user=user,
                             author=author).exists():
        Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', username=username)
