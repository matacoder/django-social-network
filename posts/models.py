from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст поста")
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации",
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор поста"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="group_posts",
        verbose_name="Группа поста"
    )

    image = models.ImageField(upload_to="posts/", blank=True, null=True)

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        # выводим кратко информацию о созданной записи
        pubdate = self.pub_date.date()
        pubauthor = self.author
        pubshort = self.text[:14]
        return (
            f"Публикация от {pubdate:%Y-%m-%d %H:%M} автора {pubauthor} "
            f"создана ({pubshort})"
        )


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="comments",
        verbose_name="Пост этого комментария"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="comments",
        verbose_name="Автор комментария"
    )
    text = models.TextField(verbose_name="Текст комментария")
    created = models.DateTimeField(
        verbose_name="Дата комментария",
        auto_now_add=True
    )

    def __str__(self):
        # выводим кратко информацию о созданном комментарии
        pubdate = self.created.date()
        pubauthor = self.author
        pubshort = self.text[:14]
        return (
            f"Комментарий от {pubdate:%Y-%m-%d %H:%M} автора {pubauthor} "
            f"создан ({pubshort})"
        )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="follower",
        verbose_name="Кто подписался"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="following",
        verbose_name="На кого подписался"
    )

    class Meta:
        unique_together = ["user", "author"]
        unique_together = ["author", "user"]
