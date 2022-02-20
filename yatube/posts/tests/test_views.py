import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

CREATED_POST_AMOUNT = 15
CONST_POST_ON_PAGE = 10


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.user = User.objects.create_user(username="testusername")
        cls.group = Group.objects.create(
            title="Test title",
            slug="test-slug",
            description="test description",
        )
        cls.post = Post.objects.create(
            text="тестовый текст",
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text="test comment text",
        )
        cls.addresses_templates = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_post", args=["test-slug"]
            ): "posts/group_list.html",
            reverse(
                "posts:profile", args=["testusername"]
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", args=[f"{cls.post.id}"]
            ): "posts/post_detail.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse(
                "posts:post_edit", args=[f"{cls.post.id}"]
            ): "posts/create_post.html",
            reverse("posts:follow_index"): "posts/follow.html",
        }
        cls.post_appears_urls = [
            reverse("posts:index"),
            reverse("posts:group_post", args=[cls.group.slug]),
            reverse("posts:profile", args=[cls.user.username]),
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTest.user)
        cache.clear()

    def test_pages_use_correct_templates(self):
        """URL-адрес profile_follow использует соответсвующий шаблоны"""
        addresses_templates = PostViewsTest.addresses_templates
        for address, template in addresses_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_first_page_contains_ten_records(self):
        """На соответсвующей странице паджинатор показывает 10 постов"""
        for i in range(CREATED_POST_AMOUNT):
            Post.objects.create(
                text=f"{i} Test post text",
                author=self.user,
                group=self.group,
            )
        for url in PostViewsTest.post_appears_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_page_contains_6_records(self):
        """На соответсвующей странице паджинатор на 2 странице показывает
        6 постов"""
        for i in range(CREATED_POST_AMOUNT):
            Post.objects.create(
                text=f"{i} Test post text",
                author=self.user,
                group=self.group,
            )
        for url in PostViewsTest.post_appears_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url + "?page=2")
                self.assertEqual(len(response.context["page_obj"]), 6)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        group = PostViewsTest.group
        response = self.authorized_client.get(
            reverse("posts:group_post", args=["test-slug"])
        )
        self.assertEqual(response.context["group"], group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        for i in range(CREATED_POST_AMOUNT):
            Post.objects.create(
                text=f"{i} Test post text",
                author=PostViewsTest.user,
                group=PostViewsTest.group,
            )
        response = self.authorized_client.get(
            reverse("posts:profile", args=["testusername"]) + "?page=1"
        )
        author = PostViewsTest.user
        page_obj = author.posts.order_by("-pub_date")[:10]
        self.assertEqual(response.context["author"], author)
        self.assertEqual(response.context["post_count"], 16)
        self.assertEqual(
            response.context.get("page_obj").object_list, list(page_obj)
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        post = PostViewsTest.post
        response = self.authorized_client.get(
            reverse("posts:post_detail", args=[post.id])
        )
        self.assertEqual(response.context["post"], post)
        self.assertEqual(response.context["post_count"], 1)
        self.assertEqual(response.context["title"], "тестовый текст")

    def test_post_create_get_show_correct_form_in_context(self):
        """Шаблон post_create при get запросе сформирован с правильной формой
        в контексте."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edite_get_show_correct_from_in_context(self):
        """Шаблон post_edit при get запросе сформирован с правильной формой
        в контексте."""
        post = self.post
        response = self.authorized_client.get(
            reverse("posts:post_edit", args=[post.id])
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_appears_on_page(self):
        """Пост появляется на соотв-й странице, если при создании
        поста указать группу"""
        post = Post.objects.create(
            text="Test post text",
            author=PostViewsTest.user,
            group=PostViewsTest.group,
        )
        for url in PostViewsTest.post_appears_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                first_object = response.context["page_obj"][0]
                self.assertEqual(first_object, post)

    def test_post_with_image_appears_on_page(self):
        """При выводе поста с картинкой изображение передаётся в словаре context
        на главную страницу, на страницу профайла, на страницу группы"""
        post = Post.objects.create(
            text="Test post text",
            author=PostViewsTest.user,
            group=PostViewsTest.group,
            image=PostViewsTest.uploaded,
        )
        for url in PostViewsTest.post_appears_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                first_object = response.context["page_obj"][0]
                self.assertEqual(first_object, post)
                self.assertEqual(first_object.image, post.image)

    def test_post_with_image_appears_on_post_detail_page(self):
        """При выводе поста с картинкой на отдельную страницу поста изображение
        передаётся в словаре context."""
        post = Post.objects.create(
            text="Test post text",
            author=PostViewsTest.user,
            group=PostViewsTest.group,
            image=PostViewsTest.uploaded,
        )
        response = self.authorized_client.get(
            reverse("posts:post_detail", args=[f"{post.id}"])
        )
        self.assertEqual(response.context["post"].image, post.image)

    def test_after_submission_comment_appears_on_page(self):
        """После успешной отправки комментарий появляется на странице поста."""
        comment = Comment.objects.create(
            post=PostViewsTest.post,
            author=PostViewsTest.user,
            text="2 test comment text",
        )
        response = self.authorized_client.get(
            reverse("posts:post_detail", args=[f"{PostViewsTest.post.id}"])
        )
        comment_count = Comment.objects.filter(
            post=PostViewsTest.post
        ).count()
        last_comment = response.context["comments"][comment_count - 1]
        self.assertEqual(last_comment, comment)
        self.assertEqual(last_comment.text, "2 test comment text")

    def test_index_page_cache_content(self):
        """Проверка кэширования главной страницы."""
        Post.objects.create(
            text="2 Test post text",
            author=PostViewsTest.user,
            group=PostViewsTest.group,
        )
        post = Post.objects.create(
            text="Test post text",
            author=PostViewsTest.user,
            group=PostViewsTest.group,
        )
        response = self.authorized_client.get(reverse("posts:index"))
        context = response.context
        content = response.content
        first_object = context["page_obj"][0]
        self.assertEqual(first_object, post)
        post.delete()
        response = self.authorized_client.get(reverse("posts:index"))
        new_content = response.content
        self.assertEqual(new_content, content)
        cache.clear()
        response = self.authorized_client.get(reverse("posts:index"))
        new_new_content = response.content
        self.assertNotEqual(new_new_content, content)

    def test_authorized_user_can_subscribe_to_other_users(self):
        """Авторизованный пользователь может подписываться на других п-телей"""
        follower_user = User.objects.create_user(username="follower")
        followed_user = User.objects.create_user(username="followed")
        follower_client = Client()
        follower_client.force_login(follower_user)
        following = Follow.objects.filter(
            user=follower_user, author=followed_user
        ).exists()
        self.assertFalse(following)
        response = follower_client.get("/profile/followed/follow/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        following = Follow.objects.filter(
            user=follower_user, author=followed_user
        ).exists()
        self.assertTrue(following)

    def test_authorized_user_can_unsubscribe_from_other_users(self):
        """Авторизованный пользователь может отписываться от других п-телей"""
        follower_user = User.objects.create_user(username="follower")
        followed_user = User.objects.create_user(username="followed")
        follower_client = Client()
        follower_client.force_login(follower_user)
        Follow.objects.create(
            user=follower_user,
            author=followed_user,
        )
        following = Follow.objects.filter(
            user=follower_user,
            author=followed_user,
        ).exists()
        self.assertTrue(following)
        response = follower_client.get("/profile/followed/unfollow/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        following = Follow.objects.filter(
            user=follower_user, author=followed_user
        ).exists()
        self.assertFalse(following)

    def test_new_post_appears_in_subscriber_feed(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        follower_user = User.objects.create_user(username="follower")
        followed_user = User.objects.create_user(username="followed")
        follower_client = Client()
        follower_client.force_login(follower_user)
        post = Post.objects.create(
            text="follow test text",
            author=followed_user,
            group=PostViewsTest.group,
        )
        Follow.objects.create(
            user=follower_user,
            author=followed_user,
        )
        response = follower_client.get("/follow/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        first_object = response.context["page_obj"][0]
        self.assertEqual(first_object, post)

    def test_new_post_not_appearing_in_non_subscriber_feed(self):
        """Новая запись пользователя не появляется в ленте тех, кто на него
        не подписан."""
        follower_user = User.objects.create_user(username="follower")
        followed_user = User.objects.create_user(username="followed")
        notfollowed_user = User.objects.create_user(username="notfollowed")
        follower_client = Client()
        follower_client.force_login(follower_user)
        Post.objects.create(
            text="follow test text",
            author=followed_user,
            group=PostViewsTest.group,
        )
        notfollowed_post = Post.objects.create(
            text="follow test text",
            author=notfollowed_user,
            group=PostViewsTest.group,
        )
        Follow.objects.create(
            user=follower_user,
            author=followed_user,
        )
        response = follower_client.get("/follow/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        first_object = response.context["page_obj"][0]
        self.assertNotEqual(first_object, notfollowed_post)

    def test_you_cant_follow_yourself(self):
        """Нельзя подписаться на самого себя"""
        follower_user = User.objects.create_user(username="follower")
        follower_client = Client()
        follower_client.force_login(follower_user)
        response = follower_client.get("/profile/follower/follow/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        following = Follow.objects.filter(
            user=follower_user, author=follower_user
        ).exists()
        self.assertFalse(following)

    def test_(self):
        """Проверьте, что вы можете подписаться на пользователя только один раз"""