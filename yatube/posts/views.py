from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import paginator_util


def index(request):
    post_list = Post.objects.select_related(
        'group',
        'author'
    ).prefetch_related(
        'comments'
    ).all()
    page_obj = paginator_util(post_list, request)
    return render(
        request,
        'posts/index.html',
        {'page_obj': page_obj}
    )


def group_posts(request, slug: str):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginator_util(post_list, request)
    return render(
        request,
        'posts/group_list.html',
        {'page_obj': page_obj, 'group': group}
    )


def profile(request, username: str):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginator_util(post_list, request)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    return render(
        request,
        'posts/profile.html',
        {
            'page_obj': page_obj,
            'author': author,
            'following': following
        }
    )


def post_detail(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post,
            'comments': comments,
            'form': form
        }
    )


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not request.method == "POST":
        return render(
            request,
            'posts/create_post.html',
            {'form': form}
        )
    if not form.is_valid():
        return render(
            request,
            'posts/create_post.html',
            {'form': form}
        )

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(
            request,
            'posts/create_post.html',
            {
                'form': form,
                'is_edit': True,
                'post': post
            }
        )

    form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.select_related(
        'group',
        'author'
    ).prefetch_related(
        'comments'
    ).filter(author__following__user=request.user)
    page_obj = paginator_util(post_list, request)
    return render(
        request,
        'posts/follow.html',
        {'page_obj': page_obj}
    )


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)
