from django.core.cache import cache
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow

from django.core.paginator import Paginator, Page
from posts.forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required

POSTS_ON_PAGE: int = 10
CACHE_TIMEOUT: int = 20


class CachedPaginator(Paginator):
    """A paginator that caches the results on a page by page basis."""
    def __init__(self,
                 object_list,
                 per_page,
                 cache_key,
                 cache_timeout=300,
                 orphans=0,
                 allow_empty_first_page=True):
        super(CachedPaginator, self).__init__(object_list,
                                              per_page,
                                              orphans,
                                              allow_empty_first_page)
        self.cache_key = cache_key
        self.cache_timeout = cache_timeout

    def page(self, number):
        """
        Returns a Page object for the given 1-based page number.

        This will attempt to pull the results out of the cache first, based on
        the number of objects per page and the requested page number. If not
        found in the cache, it will pull a fresh list and then cache that
        result.
        """
        if number is None:
            number = 1
        number = self.validate_number(number)
        cached_object_list = cache.get(self.build_cache_key(number), None)

        if cached_object_list is not None:
            page = Page(cached_object_list, number, self)
        else:
            page = super(CachedPaginator, self).page(number)
            # Since the results are fresh, cache it.
            cache.set(self.build_cache_key(number),
                      page.object_list,
                      self.cache_timeout)

        return page

    def build_cache_key(self, page_number):
        """Appends the relevant pagination bits to the cache key."""
        return "%s:%s:%s" % (self.cache_key, self.per_page, page_number)


def create_page(posts: Post,
                page_number: int,
                posts_on_page: int,
                cache_key: str) -> Page:
    paginator = CachedPaginator(posts,
                                posts_on_page,
                                cache_key,
                                CACHE_TIMEOUT
                                )
    page_obj = paginator.page(page_number)
    return page_obj


def create_page_not_cached(posts: Post,
                           page_number: int,
                           posts_on_page: int) -> Page:
    paginator = Paginator(posts, posts_on_page)
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('group').all()
    page_number = request.GET.get('page')
    page_obj = create_page(posts, page_number, POSTS_ON_PAGE, 'index_page')
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_number = request.GET.get('page')
    page_obj = create_page(posts,
                           page_number,
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
    page_number = request.GET.get('page')
    page_obj = create_page(posts,
                           page_number,
                           POSTS_ON_PAGE,
                           f'profile_page_{username}')
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=user).exists()
    else:
        following = None
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
    author_posts = post.author.posts.all()
    comments = post.comments.all()
    context = {
        'post': post,
        'author_posts': author_posts,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    groups = Group.objects.all()
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    context = {
        'form': form,
        'groups': groups,
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
    groups = Group.objects.all()
    post = Post.objects.get(pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    context = {
        'form': form,
        'groups': groups,
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
    page_number = request.GET.get('page')
    page_obj = create_page_not_cached(posts, page_number, POSTS_ON_PAGE)
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
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', username=username)
