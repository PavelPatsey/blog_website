from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User

CONST_POST_ON_PAGE = 10


@cache_page(20)
def index(request):
    post_list = Post.objects.all().order_by("-pub_date")
    paginator = Paginator(post_list, CONST_POST_ON_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.order_by("-pub_date")
    paginator = Paginator(post_list, CONST_POST_ON_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.order_by("-pub_date")
    post_count = post_list.count()
    paginator = Paginator(post_list, CONST_POST_ON_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "author": author,
        "post_count": post_count,
        "page_obj": page_obj,
    }
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    context["following"] = following
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post_count = post.author.posts.count()
    comments = Comment.objects.filter(post=post)
    title = post.text[:30]
    form = CommentForm()
    context = {
        "post": post,
        "post_count": post_count,
        "title": title,
        "form": form,
        "comments": comments,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    template = "posts/create_post.html"
    action_link = reverse("posts:post_create")
    group_list = Group.objects.all()
    context = {
        "title": "Новый пост",
        "card_header_name": "Новый пост",
        "small_name": "Текст нового поста",
        "button_name": "Создать",
        "action_link": action_link,
        "text": "",
        "group_list": group_list,
    }
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:profile", post.author)
    context["form"] = form
    return render(request, template, context)


def post_author_only(func):
    def check_author(request, post_id, *args, **kwargs):
        post = get_object_or_404(Post, id=post_id)
        if request.user == post.author:
            return func(request, post_id, *args, **kwargs)
        return redirect("posts:post_detail", post_id)

    return check_author


@post_author_only
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    template = "posts/create_post.html"
    action_link = reverse("posts:post_edit", args=[post_id])
    group_list = Group.objects.all()
    context = {
        "title": "Редактирвоать пост",
        "card_header_name": "Редактировать пост",
        "small_name": "Текст редактируемого поста",
        "button_name": "Сохранить",
        "action_link": action_link,
        "text": "",
        "group_list": group_list,
    }
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        text = form.cleaned_data["text"]
        group = form.cleaned_data["group"]
        image = form.cleaned_data["image"]
        post.text = text
        post.group = group
        post.image = image
        post.save()
        return redirect("posts:post_detail", post_id)
    context["form"] = form
    context["text"] = form.instance.text
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    authors = request.user.follower.all().values("author")
    post_list = Post.objects.filter(author__in=authors).order_by("-pub_date")
    paginator = Paginator(post_list, CONST_POST_ON_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.create(
        user=request.user,
        author=author,
    )
    return redirect("posts:profile", username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, author=author)
    follow.delete()
    return redirect("posts:profile", username)
