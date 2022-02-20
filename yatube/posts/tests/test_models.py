from django.test import TestCase

from ..models import Comment, Follow, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="testusername")
        cls.follower = User.objects.create_user(username="follower")
        cls.following = User.objects.create_user(username="following")
        cls.group = Group.objects.create(
            title="Test title",
            slug="test-slug",
            description="test description",
        )
        cls.post = Post.objects.create(text="тестовый текст", author=cls.user)
        cls.comment = Comment.objects.create(
            post=cls.post, author=cls.user, text="test comment text"
        )
        cls.follow = Follow(user=cls.follower, author=cls.following)
        cls.test_str_data = [
            (cls.post, "тестовый текст"),
            (Post(), ""),
            (
                Post(text="очень длинный текст больше 15 символов"),
                "очень длинный т",
            ),
            (cls.group, "Test title"),
            (Group(), ""),
            (cls.comment, "test comment te"),
            (Comment(), ""),
            (cls.follow, "follower_to_following"),
        ]
        cls.verbose_names_valuses = {
            Post.author.field.verbose_name: "Автор",
            Post.group.field.verbose_name: "Группа",
        }

    def test_models_have_correct_str_method(self):
        """Проверяем, что у моделей корректно работает __str__."""
        for obj, res in PostModelTest.test_str_data:
            with self.subTest(obj=obj):
                self.assertEqual(str(obj), res)

    def test_models_verbose_name(self):
        """Проверяем что у моделей работает verbose name"""
        for (
            verbose_name,
            value,
        ) in PostModelTest.verbose_names_valuses.items():
            with self.subTest(verbose_name=verbose_name):
                self.assertEqual(verbose_name, value)

    def test_post_text_help_text(self):
        """Проверяем что help text работает для модели Post"""
        self.assertEqual(
            Post._meta.get_field("text").help_text, "Введите текст поста"
        )
