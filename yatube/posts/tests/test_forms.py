import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import reverse
from django.test import Client, TestCase, override_settings
from django.core.cache import cache

from posts.models import Group, Post, Comment

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostFormTests(TestCase):
    """Форма записи работает корректно."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        User = get_user_model()  # noqa
        cls.user = User.objects.create(username="test_user")

        cls.group = Group.objects.create(
            title="Заголовок тестовой группы",
            slug="test_group",
            description="Описание тестовой группы"
        )

        cls.post = Post.objects.create(
            text="Оригинальный текст",
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.client.force_login(PostFormTests.user)

        self.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        self.uploaded = SimpleUploadedFile(
            name="small.gif",
            content=self.small_gif,
            content_type="image/gif"
        )

    def test_post_without_group_creation(self):
        """Новая запись без группы корректно создается."""
        posts_count = Post.objects.count()

        form_data = {
            "text": "Пост без группы",
        }

        response = self.client.post(
            path=reverse("new_post"),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                author=PostFormTests.user,
                group=None
            ).exists()
        )

    def test_post_with_group_creation(self):
        """Новая запись с группой корректно создается."""
        posts_count = Post.objects.count()

        form_data = {
            "text": "Пост с группой",
            "group": PostFormTests.group.pk
        }

        response = self.client.post(
            path=reverse("new_post"),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                author=PostFormTests.user,
                group=PostFormTests.group
            ).exists()
        )

    def test_post_with_image_creation(self):
        """Новая запись с изображением корректно создается."""
        posts_count = Post.objects.count()

        form_data = {
            "text": "Пост с изображением",
            "image": self.uploaded,
        }

        response = self.client.post(
            path=reverse("new_post"),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                author=PostFormTests.user,
            ).exists()
        )

        new_post = Post.objects.filter(
            text="Пост с изображением",
            author=PostFormTests.user,
        ).first()

        self.assertEqual(
            new_post.image.read(),
            self.small_gif
        )

    def test_post_edit(self):
        """Запись корректно редактируется."""
        posts_count = Post.objects.count()

        form_data = {
            "text": "Отредактированый текст",
            "group": PostFormTests.group.pk,
            "image": self.uploaded,
        }

        response = self.client.post(
            path=reverse(
                "post_edit",
                kwargs={
                    "username": PostFormTests.post.author.username,
                    "post_id": PostFormTests.post.pk
                }
            ),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                "post",
                kwargs={
                    "username": PostFormTests.post.author.username,
                    "post_id": PostFormTests.post.pk
                }
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)

        PostFormTests.post.refresh_from_db()
        self.assertEqual(PostFormTests.post.text, "Отредактированый текст")
        self.assertEqual(PostFormTests.post.group, PostFormTests.group)
        self.assertEqual(
            PostFormTests.post.image.read(),
            self.small_gif
        )


class CommentsFormsTest(TestCase):
    """Комментарии работают корректно."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        User = get_user_model()  # noqa
        cls.user = User.objects.create(username="user")

        cls.post = Post.objects.create(
            text="Некоторый тестовый текст",
            author=cls.user,
        )

    def setUp(self):
        cache.clear()

        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(CommentsFormsTest.user)

        self.path = reverse(
            "add_comment",
            kwargs={
                "username": CommentsFormsTest.user.username,
                "post_id": CommentsFormsTest.post.pk,
            }
        )

        self.form_data = {
            "text": "Комментарий",
        }

    def test_authorized_client_can_add_comments(self):
        """Авторизованный пользователь может добавлять комментарии."""
        self.authorized_client.post(
            path=self.path,
            data=self.form_data,
            follow=True
        )

        self.assertTrue(
            Comment.objects.filter(
                post=CommentsFormsTest.post,
                author=CommentsFormsTest.user,
                text=self.form_data["text"]
            ).exists()
        )

    def test_guest_client_cant_add_comments(self):
        """Неавторизованный пользователь не может добавлять комментарии."""
        self.guest_client.post(
            path=self.path,
            data=self.form_data,
            follow=True
        )

        self.assertFalse(
            Comment.objects.filter(
                post=CommentsFormsTest.post,
                author=CommentsFormsTest.user,
                text=self.form_data["text"]
            ).exists()
        )
