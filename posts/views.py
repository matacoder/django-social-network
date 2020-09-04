import random

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render, reverse

from .forms import PostForm, CommentForm
from .models import Group, Post, User
from functools import lru_cache
from django.views.decorators.cache import cache_page


@cache_page(20)
def index(request):
    username = request.user
    post_list = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    # показывать по 10 записей на странице.
    page_number = request.GET.get("page")
    # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)
    # получить записи с нужным смещением
    return render(
        request,
        "posts/index.html",
        {
            "page": page,
            "paginator": paginator,
            "profile": profile_extract(username)
        }
    )


def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    url = reverse(
        "post_single",
        kwargs={"username": username, "post_id": post_id}
    )
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            form.instance.author = request.user
            form.instance.post = post
            form.save()
            return redirect(url)
    form = CommentForm()
    return redirect(url)


# @cache_page(60 * 15)
def group_posts(request, slug):
    username = request.user
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request, "posts/group.html",
        {
            "page": page,
            "paginator": paginator,
            "group": group,
            "profile": profile_extract(username)}
    )


@login_required
def new_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES)
        if form.is_valid():
            form.instance.author = request.user
            form.save()
            url = reverse('index')
            return redirect(url)
    form = PostForm()
    labels = {
        "title": "Новая запись",
        "button": "Добавить новую запись"
    }
    return render(
        request, "posts/new_post.html", {"form": form, "labels": labels}
    )


@lru_cache(maxsize=None)
def profile_extract(username):
    """ Get data for profile template """
    author = get_object_or_404(User, username=username)
    # TODO: probably next sprint (randint now)
    followers = random.randint(500, 1000)
    following = random.randint(600, 2000)
    posts_count = author.posts.count()
    return {
        "author": author,
        "followers": followers,
        "following": following,
        "posts_count": posts_count
    }


# @cache_page(60 * 15)
def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request, "posts/profile.html",
        {
            "page": page,
            "paginator": paginator,
            "profile": profile_extract(username),
            "author": author
        }
    )


# @cache_page(60 * 15)
def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = get_object_or_404(User, username=username)  # pass test
    comments = post.post_comments.all()
    form = CommentForm()
    return render(
        request, "posts/post.html",
        {
            "post": post,
            "profile": profile_extract(username),
            "username": author,  # pass test
            "form": form,
            "items": comments
        }
    )


@login_required
def post_edit(request, username, post_id):
    template_name = "posts/new_post.html"
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    url = reverse(
        "post_single",
        kwargs={"username": username, "post_id": post_id}
    )
    if post.author != request.user:
        return redirect(url)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if request.POST and form.is_valid():
        form.save()
        return redirect(url)

    labels = {
        "title": "Редактировать запись",
        "button": "Сохранить"
    }

    return render(
        request,
        template_name,
        {
            "form": form,
            "labels": labels,
            "post": post
        }
    )


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
