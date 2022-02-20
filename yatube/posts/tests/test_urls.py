from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Follow, Group, Post, User


class PostURLTests(TestCase):
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
        cls.url_names_templates = {
            "/": "posts/index.html",
            "/group/test-slug/": "posts/group_list.html",
            "/profile/testusername/": "posts/profile.html",
            f"/posts/{cls.post.id}/": "posts/post_detail.html",
            "/create/": "posts/create_post.html",
            f"/posts/{cls.post.id}/edit/": "posts/create_post.html",
            "/follow/": "posts/follow.html",
        }
        cls.urls_http_statuses = {
            "/": HTTPStatus.OK,
            "/group/test-slug/": HTTPStatus.OK,
            "/profile/testusername/": HTTPStatus.OK,
            f"/posts/{cls.post.id}/": HTTPStatus.OK,
            "/create/": HTTPStatus.FOUND,
            "/unexisting_page/": HTTPStatus.NOT_FOUND,
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        cache.clear()

    def test_urls_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in PostURLTests.url_names_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_pages_are_available_to_an_anonymous_user(self):
        """Проверка доступа анонимного пользователя к страницам"""
        for url, http_status in PostURLTests.urls_http_statuses.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, http_status)

    def test_post_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина."""
        response = self.guest_client.get("/create/", follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, "/auth/login/?next=/create/")

    def test_post_edite_url_redirect_anonymous(self):
        """Страница post_edit перенаправляет анонимного пользователя."""
        post = PostURLTests.post
        response = self.guest_client.get(f"/posts/{post.id}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, f"/posts/{post.id}/")

    def test_post_edite_url_redirect_anonymous_on_post_detail(self):
        """Страница post_edit перенаправит не автора поста на страницу
        информации о посте post_detail."""
        post = PostURLTests.post
        user_1 = User.objects.create(username="testusername_1")
        authorized_client_1 = Client()
        authorized_client_1.force_login(user_1)
        response = authorized_client_1.get(
            f"/posts/{post.id}/edit/",
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, f"/posts/{post.id}/")

    def test_post_edite_url_exists_at_desired_location(self):
        """Страница post_edit доступна только автору поста."""
        post = PostURLTests.post
        response = self.authorized_client.get(f"/posts/{post.id}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_follow_url_exists_at_desired_location(self):
        """Страница /follow/ доступна авторизованному пользователю."""
        response = self.authorized_client.get("/follow/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow_url_redirect_anonymous_on_admin_login(self):
        """Страница /follow/ перенаправит анонимного пользователя
        на страницу логина."""
        response = self.guest_client.get("/follow/", follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, "/auth/login/?next=/follow/")

    def test_follow_url_redirect_anonymous_on_admin_login(self):
        """Адресс profile_follow перенаправит анонимного пользователя
        на страницу логина."""
        response = self.guest_client.get(
            "/profile/testusername/follow/", follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, "/auth/login/?next=/profile/testusername/follow/"
        )

    def test_unfollow_url_redirect_anonymous_on_admin_login(self):
        """Адресс profile_unfollow перенаправит анонимного пользователя
        на страницу логина."""
        response = self.guest_client.get(
            "/profile/testusername/unfollow/", follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, "/auth/login/?next=/profile/testusername/unfollow/"
        )

    def test_follow_url_redirect_on_following_profile(self):
        """Адресс profile_follow перенаправит пользователя на страницу
        profile автора, на которого подписались."""
        response = self.authorized_client.get(
            "/profile/testusername/follow/",
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, "/profile/testusername/")

    def test_unfollow_url_redirect_on_unfollowing_profile(self):
        """Адресс profile_unfollow перенаправит пользователя на страницу
        profile автора, от которого отписались."""
        follower_user = User.objects.create_user(username="follower")
        followed_user = User.objects.create_user(username="followed")
        follower_client = Client()
        follower_client.force_login(follower_user)
        Follow.objects.create(
            user=follower_user,
            author=followed_user,
        )
        response = follower_client.get(
            "/profile/followed/unfollow/",
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, "/profile/followed/")
