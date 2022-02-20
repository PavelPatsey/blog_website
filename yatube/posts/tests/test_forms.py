import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="testusername")
        cls.group = Group.objects.create(
            title="Test title",
            slug="test-slug",
            description="test description",
        )
        cls.post = Post.objects.create(text="тестовый текст", author=cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormsTest.user)

    def test_post_create_page_creates_new_post_without_group(self):
        """На странице post_create успешно создан пост без указания группы"""
        post_count = Post.objects.count()
        form_data = {
            "text": "test form text",
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="test form text",
            ).exists()
        )

    def test_post_create_page_creates_new_post_with_group(self):
        """На странице post_create успешно создан пост с указанием группы"""
        post_count = Post.objects.count()
        form_data = {"text": "test form text", "group": self.group.id}
        response = self.authorized_client.post(
            reverse("posts:post_create"),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="test form text",
                group=self.group.id,
            ).exists()
        )

    def test_post_create_page_creates_new_post_with_image(self):
        """На странице post_create успешно создан пост с картинкой"""
        post_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "test form text",
            "group": self.group.id,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="test form text",
                group=self.group.id,
                image="posts/small.gif",
            ).exists()
        )

    def test_on_post_edit_page_successfully_edited_post(self):
        """На странице post_edit успешно отредактирован пост"""
        post = Post.objects.create(
            text="Test post text",
            author=self.user,
            group=self.group,
        )
        form_data = {"text": "New test post text", "group": self.group.id}
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=[post.id]),
            form_data,
        )
        post = Post.objects.get(id=post.id)
        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(post.text, "New test post text")

    def test_an_authorized_user_can_comment_on_posts(self):
        """Авторизованный пользователь может комментировать посты."""
        coment_count = Comment.objects.count()
        post = PostFormsTest.post
        form_data = {"text": "test comment text"}
        response = self.authorized_client.post(
            reverse("posts:add_comment", args=[post.id]),
            form_data,
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(Comment.objects.count(), coment_count + 1)
        self.assertTrue(
            Comment.objects.filter(text="test comment text").exists()
        )

    def test_anonymous_user_cannot_comment_on_posts(self):
        """Анонимный пользователь не может комментировать посты."""
        coment_count = Comment.objects.count()
        post = PostFormsTest.post
        form_data = {"text": "test comment text"}
        response = self.guest_client.post(
            reverse("posts:add_comment", args=[post.id]),
            form_data,
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f"/auth/login/?next=/posts/{post.id}/comment/"
        )
        self.assertEquals(Comment.objects.count(), coment_count)
