from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    text = models.TextField("Текст поста", help_text="Введите текст поста")
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="posts",
    )
    group = models.ForeignKey(
        "Group",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Группа",
        help_text="Выберите группу",
    )
    image = models.ImageField("Картинка", upload_to="posts/", blank=True)

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name="Публикация",
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="comments",
    )
    text = models.TextField(
        "Текст комментария", help_text="Введите текст комментария"
    )
    created = models.DateTimeField("Дата публикации", auto_now_add=True)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
        related_name="follower",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="На кого подписались",
        related_name="following",
    )

    def __str__(self):
        return f"{self.user}_to_{self.author}"
