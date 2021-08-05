from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CommentForm, PostForm
from .models import Group, Post, Follow

User = get_user_model()


@require_http_methods(["GET"])
def index(request):
    """Основная страница со всеми постами."""

    posts = cache.get(key="index_page")
    if posts is None:
        posts = Post.objects.all()
        cache.set(
            key="index_page",
            value=posts,
            timeout=20
        )

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(
        request,
        "posts/index.html",
        {
            "page": page,
        },
    )


@require_http_methods(["GET", "POST"])
@login_required(redirect_field_name="login")
def new_post(request):
    """Создание нового поста."""

    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )

    if form.is_valid():
        obj = form.save(commit=False)
        obj.author = request.user
        obj.save()

        return redirect("index")

    return render(
        request, "posts/new_edit_post.html", {"form": form, "mode": "new"}
    )


@require_http_methods(["GET"])
def group_posts(request, slug):
    """Посты определнной группы."""

    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "posts/group.html", {"group": group, "page": page})


@require_http_methods(["GET"])
def profile(request, username):
    """Профиль пользователя."""

    author = get_object_or_404(User, username=username)
    posts = author.posts.all()

    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    context = {
        "author": author,
        "page": page,
        "following": following,
    }

    return render(request, "posts/profile.html", context)


@require_http_methods(["GET", "POST"])
def post_view(request, username, post_id):
    """Страница одной конкретной записи."""

    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=author)
    comments = post.comments.all()

    form = CommentForm()

    context = {
        "author": author,
        "post": post,
        "comments": comments,
        "form": form,
    }

    return render(request, "posts/post.html", context)


@require_http_methods(["POST"])
@login_required(redirect_field_name="login")
def add_comment(request, username, post_id):
    """Добавление комментария."""
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=author)

    form = CommentForm(
        request.POST or None
    )

    if form.is_valid():
        obj = form.save(commit=False)
        obj.post = post
        obj.author = request.user
        obj.save()

    return redirect("post", username=username, post_id=post_id)


@require_http_methods(["GET", "POST"])
@login_required(redirect_field_name="login")
def post_edit(request, username, post_id):
    """Редактирование поста."""

    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect("post", username=username, post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()

        return redirect("post", username=username, post_id=post_id)

    return render(
        request, "posts/new_edit_post.html", {"form": form, "mode": "edit"}
    )


@require_http_methods(["GET", "POST"])
def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


@require_http_methods(["GET", "POST"])
def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required(redirect_field_name="login")
@require_http_methods(["GET"])
def follow_index(request):

    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(
        request,
        "posts/follow.html",
        {"page": page}
    )


@require_http_methods(["GET"])
@login_required(redirect_field_name="login")
def profile_follow(request, username):
    """Подписаться на автора."""
    author = get_object_or_404(User, username=username)

    if (
        author == request.user
        or Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    ):
        return render(
            request,
            "misc/403.html",
            {"path": request.path},
            status=403
        )

    Follow.objects.create(
        user=request.user,
        author=author,
    )

    return redirect("profile", username=username)


@require_http_methods(["GET"])
@login_required(redirect_field_name="login")
def profile_unfollow(request, username):
    """Отписаться от автора."""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user,
        author=author,
    ).delete()

    return redirect("profile", username=username)
