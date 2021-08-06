from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client, TestCase
from http import HTTPStatus
from django.core.cache import cache

from posts.models import Group, Post


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        User = get_user_model()
        cls.author_user = User.objects.create_user(username="test_author_user")
        cls.non_author_user = User.objects.create_user(
            username="test_non_author_user"
        )

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_group",
            description="Описание тестовой группы",
        )

        cls.post = Post.objects.create(
            text="Некоторый тестовый текст",
            author=cls.author_user,
            group=cls.group,
        )

        cls.url_template_map = {
            reverse("index"): "posts/index.html",
            reverse(
                "group_posts",
                kwargs={"slug": cls.group.slug},
            ): "posts/group.html",
            reverse("new_post"): "posts/new_edit_post.html",
            reverse(
                "profile",
                kwargs={"username": cls.author_user.username},
            ): "posts/profile.html",
            reverse(
                "post",
                kwargs={
                    "username": cls.post.author.username,
                    "post_id": cls.post.pk,
                }
            ): "posts/post.html",
            reverse(
                "post_edit",
                kwargs={
                    "username": cls.post.author.username,
                    "post_id": cls.post.pk,
                }
            ): "posts/new_edit_post.html",
        }

        cls.url_redirect_map = {
            reverse("new_post"): "/auth/login/?login=" + reverse("new_post"),
            reverse(
                "post_edit",
                kwargs={
                    "username": cls.post.author.username,
                    "post_id": cls.post.pk,
                }
            ): ("/auth/login/?login="
                + reverse(
                    "post_edit",
                    kwargs={
                        "username": cls.post.author.username,
                        "post_id": cls.post.pk,
                    }
                )
                )
        }

    def setUp(self):
        cache.clear()

        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(URLTests.author_user)

        self.authorized_client_non_author = Client()
        self.authorized_client_non_author.force_login(URLTests.non_author_user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for (url, template) in URLTests.url_template_map.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_url_redirect(self):
        """Переадресация для неавторизованных клиентов."""
        for url, redirect_url in URLTests.url_redirect_map.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_post_edit_redirect(self):
        """Переадресация со страницы редактирования записи
        для пользователя, не являющегося автором этой записи."""
        url = reverse(
            "post_edit",
            kwargs={
                "username": URLTests.post.author.username,
                "post_id": URLTests.post.pk,
            }
        )
        redirect_url = reverse(
            "post",
            kwargs={
                "username": URLTests.post.author.username,
                "post_id": URLTests.post.pk,
            },
        )

        response = self.authorized_client_non_author.get(url)
        self.assertRedirects(
            response, redirect_url
        )

    def test_uncorrect_url_response_404(self):
        """Некорретный url возвращает ошибку 404."""
        url = "/some_incorrect_url/"
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
