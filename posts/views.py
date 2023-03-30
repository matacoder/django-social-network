from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20, key_prefix="index_page")
def index(request):
    post_list = (
        Post.objects.select_related("author", "group").order_by("-pub_date").all()
    )

    paginator = Paginator(post_list, 10)
    # показывать по 10 записей на странице.
    page_number = request.GET.get("page")
    # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)
    # получить записи с нужным смещением
    return render(request, "posts/index.html", {"page": page, "paginator": paginator})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    url = reverse("post_single", kwargs={"username": username, "post_id": post_id})
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            form.instance.author = request.user
            form.instance.post = post
            form.save()
            return redirect(url)
    form = CommentForm()
    return redirect(url)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "posts/group.html",
        {"page": page, "paginator": paginator, "group": group},
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.instance.author = request.user
        form.save()
        url = reverse("index")
        return redirect(url)
    labels = {"title": "Новая запись", "button": "Добавить новую запись"}
    return render(request, "posts/new_post.html", {"form": form, "labels": labels})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        user = request.user

        if Follow.objects.filter(user=user, author=author):
            following = True

    return render(
        request,
        "posts/profile.html",
        {
            "page": page,
            "paginator": paginator,
            "author": author,
            "following": following,
        },
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    comments = post.comments.all()
    form = CommentForm()
    return render(
        request,
        "posts/post.html",
        {"post": post, "author": author, "form": form, "items": comments},
    )


@login_required
def post_edit(request, username, post_id):
    template_name = "posts/new_post.html"
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    url = reverse("post_single", kwargs={"username": username, "post_id": post_id})
    if post.author != request.user:
        return redirect(url)

    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)

    if request.POST and form.is_valid():
        form.save()
        return redirect(url)

    labels = {"title": "Редактировать запись", "button": "Сохранить"}

    return render(
        request, template_name, {"form": form, "labels": labels, "post": post}
    )


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    logged = request.user

    # 1. Get author object of post
    # 2. Get posts "following" of author via related name
    # 3. Where user = logged.
    posts = Post.objects.filter(author__following__user=logged)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "posts/follow.html",
        {"page": page, "paginator": paginator, "username": logged},
    )


@login_required
def profile_follow(request, username):
    url = reverse("profile", args=[username])
    user = request.user
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=user, author=author).exists():
        return redirect(url)
    if author == user:
        return redirect(url)
    Follow.objects.create(user=user, author=author)
    return redirect(url)


@login_required
def profile_unfollow(request, username):
    url = reverse("profile", args=[username])
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect(url)
