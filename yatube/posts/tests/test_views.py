import shutil
import tempfile

from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import reverse
from django.test import Client, TestCase, override_settings

from posts.models import Group, Post, Follow

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ViewTests(TestCase):
    """View-функции работают корректно."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_group",
            description="Описание тестовой группы",
        )

        cls.group_not_for_post = Group.objects.create(
            title="Группа не для поста",
            slug="group_not_for_post",
            description="Описание группы не для поста",
        )

        User = get_user_model() # noqa
        cls.user = User.objects.create(username="test_user")

        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif"
        )

        cls.post = Post.objects.create(
            text="Некоторый тестовый текст",
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

        cls.url_template_map = {
            reverse("index"): "posts/index.html",
            reverse(
                "group_posts", kwargs={"slug": cls.group.slug}
            ): "posts/group.html",
            reverse("new_post"): "posts/new_edit_post.html",
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.post_display = {
            reverse("index"): Post.objects.count() % 10,
            reverse("group_posts", kwargs={"slug": ViewTests.group.slug}):
                Post.objects.count() % 10,
            reverse(
                "group_posts",
                kwargs={"slug": ViewTests.group_not_for_post.slug},
            ): 0,
        }

        self.authorized_client = Client()
        self.authorized_client.force_login(ViewTests.user)

        self.context_type_user = type(get_user_model())
        self.context_type_name_user = type(ViewTests.user).__name__

        self.context_type_group = type(Group)
        self.context_type_name_group = type(ViewTests.group).__name__

        self.context_type_post = type(Post)
        self.context_type_name_post = type(ViewTests.post).__name__

        self.context_type_post_form = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }

        self.context_data = {
            "group": {
                "title": ViewTests.group.title,
                "slug": ViewTests.group.slug,
                "description": ViewTests.group.description,
            },
            "post": {
                "text": ViewTests.post.text,
                "author": ViewTests.post.author,
                "pub_date": ViewTests.post.pub_date,
                "group": ViewTests.post.group,
                "image": ViewTests.post.image
            },
            "mode_new_post": "new",
            "form_edit": {
                "text": ViewTests.post.text,
                "author": ViewTests.post.author,
                "image": ViewTests.post.image,
            },
            "mode_edit_post": "edit",
        }

    def test_post_display_correct(self):
        """Созданный пост корректно отображается на страницах."""
        for url, posts_count in self.post_display.items():
            response = self.authorized_client.get(url)
            self.assertEqual(len(response.context["page"]), posts_count)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("index"))
        first_object = response.context["page"][0]

        self.assertIsInstance(type(first_object), self.context_type_post)
        self.assertEqual(
            type(first_object).__name__, self.context_type_name_post
        )

        self.assertEqual(first_object.text, self.context_data["post"]["text"])
        self.assertEqual(
            first_object.author, self.context_data["post"]["author"]
        )
        self.assertEqual(
            first_object.pub_date, self.context_data["post"]["pub_date"]
        )
        self.assertEqual(
            first_object.group, self.context_data["post"]["group"]
        )
        self.assertEqual(
            first_object.image, self.context_data["post"]["image"]
        )

    def test_group_posts_page_shows_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        url = reverse("group_posts", kwargs={"slug": ViewTests.group.slug})
        response = self.authorized_client.get(url)
        response_group = response.context["group"]
        response_post = response.context["page"][0]

        self.assertIsInstance(type(response_group), self.context_type_group)
        self.assertIsInstance(type(response_post), self.context_type_post)

        self.assertEqual(
            type(response_group).__name__, self.context_type_name_group
        )
        self.assertEqual(
            type(response_post).__name__, self.context_type_name_post
        )

        self.assertEqual(
            response_group.title, self.context_data["group"]["title"]
        )
        self.assertEqual(
            response_group.slug, self.context_data["group"]["slug"]
        )
        self.assertEqual(
            response_group.description,
            self.context_data["group"]["description"],
        )

        self.assertEqual(response_post.text, self.context_data["post"]["text"])
        self.assertEqual(
            response_post.author, self.context_data["post"]["author"]
        )
        self.assertEqual(
            response_post.pub_date, self.context_data["post"]["pub_date"]
        )
        self.assertEqual(
            response_post.group, self.context_data["post"]["group"]
        )
        self.assertEqual(
            response_post.image, self.context_data["post"]["image"]
        )

    def test_new_post_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("new_post"))

        for field_name, field_type in self.context_type_post_form.items():
            with self.subTest(field_name=field_name):
                form_field = response.context["form"].fields[field_name]
                self.assertIsInstance(form_field, field_type)

        self.assertEqual(
            response.context["mode"], self.context_data["mode_new_post"]
        )

    def test_post_edit_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        url = reverse(
            "post_edit",
            kwargs={
                "username": ViewTests.post.author.username,
                "post_id": ViewTests.post.pk
            }
        )
        response = self.authorized_client.get(url)
        for field_name, field_type in self.context_type_post_form.items():
            with self.subTest(field_name=field_name):
                form_field = response.context["form"].fields[field_name]
                self.assertIsInstance(form_field, field_type)

        self.assertEqual(
            response.context["form"].instance.text,
            self.context_data["form_edit"]["text"]
        )
        self.assertEqual(
            response.context["form"].instance.author,
            self.context_data["form_edit"]["author"]
        )

        self.assertEqual(
            response.context["mode"], self.context_data["mode_edit_post"]
        )

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        url = reverse("profile", kwargs={"username": ViewTests.user.username})
        response = self.authorized_client.get(url)
        response_author = response.context["author"]
        response_post = response.context["page"][0]

        self.assertIsInstance(type(response_author), self.context_type_user)
        self.assertIsInstance(type(response_post), self.context_type_post)

        self.assertEqual(
            type(response_author).__name__, self.context_type_name_user
        )
        self.assertEqual(
            type(response_post).__name__, self.context_type_name_post
        )

        self.assertEqual(
            response_author.username, ViewTests.user.username
        )

        self.assertEqual(response_post.text, self.context_data["post"]["text"])
        self.assertEqual(
            response_post.author, self.context_data["post"]["author"]
        )
        self.assertEqual(
            response_post.pub_date, self.context_data["post"]["pub_date"]
        )
        self.assertEqual(
            response_post.group, self.context_data["post"]["group"]
        )
        self.assertEqual(
            response_post.image, self.context_data["post"]["image"]
        )

    def test_post_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        url = reverse("post", kwargs={
            "username": ViewTests.user.username,
            "post_id": ViewTests.post.pk
        })
        response = self.authorized_client.get(url)
        response_author = response.context["author"]
        response_post = response.context["post"]

        self.assertIsInstance(type(response_author), self.context_type_user)
        self.assertIsInstance(type(response_post), self.context_type_post)

        self.assertEqual(
            type(response_author).__name__, self.context_type_name_user
        )
        self.assertEqual(
            type(response_post).__name__, self.context_type_name_post
        )

        self.assertEqual(
            response_author.username, ViewTests.user.username
        )

        self.assertEqual(response_post.text, self.context_data["post"]["text"])
        self.assertEqual(
            response_post.author, self.context_data["post"]["author"]
        )
        self.assertEqual(
            response_post.pub_date, self.context_data["post"]["pub_date"]
        )
        self.assertEqual(
            response_post.group, self.context_data["post"]["group"]
        )
        self.assertEqual(
            response_post.image, self.context_data["post"]["image"]
        )


class CacheTest(TestCase):
    """Корректность кэширования."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        User = get_user_model()  # noqa
        cls.user = User.objects.create(username="test_user")

    def setUp(self):
        self.client = Client()
        self.client.force_login(CacheTest.user)

    def test_cashe_index(self):
        """Кэширование главной страницы."""
        url = reverse("index")
        response = self.client.get(url)

        posts_count_old = len(response.context["page"])

        Post.objects.create(
            text="Проверка кэширования",
            author=CacheTest.user
        )

        response = self.client.get(url)
        self.assertEqual(len(response.context["page"]), posts_count_old)

        cache.clear()
        response = self.client.get(url)
        self.assertEqual(
            len(response.context["page"].object_list),
            posts_count_old + 1
        )


class PaginatorViewsTest(TestCase):
    """Пажинатор работает корректно."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

        User = get_user_model()  # noqa
        cls.user = User.objects.create(username="test_user")

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_group",
            description="Описание тестовой группы",
        )

        posts_list = [
            Post(
                text="Некоторый тестовый текст",
                author=cls.user,
                group=cls.group,
            )
        ] * 13

        Post.objects.bulk_create(posts_list)

        cls.posts_count_per_page = {
            reverse("index"): (10, 3),
            reverse("group_posts", kwargs={"slug": cls.group.slug}): (10, 3),
            reverse("profile", kwargs={"username": cls.user.username}): (
                10,
                3,
            ),
        }

    def setUp(self):
        self.client = Client()
        self.client.force_login(PaginatorViewsTest.user)

    def test_pages_contains_correct_records_count(self):
        """Число записей на страницах корректно."""
        for (
            url,
            posts_count,
        ) in PaginatorViewsTest.posts_count_per_page.items():
            with self.subTest(url=url):
                first_page = self.client.get(url)
                second_page = self.client.get(url + "?page=2")
                self.assertEqual(
                    len(first_page.context["page"]), posts_count[0]
                )
                self.assertEqual(
                    len(second_page.context["page"]), posts_count[1]
                )


class FollowViewsTest(TestCase):
    """Подписки работают корректно."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

        User = get_user_model()  # noqa
        cls.user = User.objects.create(username="user")
        cls.author = User.objects.create(username="author")

        cls.post = Post.objects.create(
            text="Некоторый тестовый текст",
            author=cls.author,
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(FollowViewsTest.user)

        Follow.objects.all().delete()

    def test_authorized_client_can_start_following(self):
        """Авторизованный пользователь может подписаться на автора."""
        url = reverse(
            "profile_follow",
            kwargs={"username": FollowViewsTest.author.username}
        )
        self.authorized_client.get(url)
        self.assertTrue(
            Follow.objects.filter(
                user=FollowViewsTest.user,
                author=FollowViewsTest.author
            ).exists()
        )

    def test_authorized_client_can_stop_following(self):
        """Авторизованный пользователь может отписаться от автора."""
        Follow.objects.create(
            user=FollowViewsTest.user,
            author=FollowViewsTest.author
        )

        url = reverse(
            "profile_unfollow",
            kwargs={"username": FollowViewsTest.author.username}
        )
        self.authorized_client.get(url)
        self.assertFalse(
            Follow.objects.filter(
                user=FollowViewsTest.user,
                author=FollowViewsTest.author
            ).exists()
        )

    def test_double_following_forbidden(self):
        """Нельзя два раза подписаться на одного автора."""
        url = reverse(
            "profile_follow",
            kwargs={"username": FollowViewsTest.author.username}
        )
        self.authorized_client.get(url)
        self.authorized_client.get(url)

        self.assertEqual(
            Follow.objects.filter(
                user=FollowViewsTest.user,
                author=FollowViewsTest.author
            ).count(),
            1
        )

    def test_user_cant_follow_yourself(self):
        """Нельзя подписаться на самого себя."""
        url = reverse(
            "profile_follow",
            kwargs={"username": FollowViewsTest.user.username}
        )
        self.authorized_client.get(url)

        self.assertFalse(
            Follow.objects.filter(
                user=FollowViewsTest.user,
                author=FollowViewsTest.user
            ).exists()
        )

    def test_user_get_following_posts(self):
        """Пользователь получает в ленте записи авторов
        на которых он подписан."""
        url = reverse(
            "profile_follow",
            kwargs={"username": FollowViewsTest.author.username}
        )
        self.authorized_client.get(url)

        response = self.authorized_client.get(reverse("follow_index"))

        self.assertEqual(len(response.context["page"]), 1)

    def test_user_get_following_posts(self):
        """Пользователь не получает в ленте записи авторов
        на которых он не подписан."""
        response = self.authorized_client.get(reverse("follow_index"))

        self.assertEqual(len(response.context["page"]), 0)
