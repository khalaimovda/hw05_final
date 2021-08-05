from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post
from django.core.cache import cache

class GroupModelTest(TestCase):
    """Тест модели Group"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

        cls.group = Group(
            title="Тестовая группа",
            slug="test_group",
            description="Описание тестовой группы",
        )

    def test_str(self):
        """__str__ в модели совпадает с ожидаемым"""
        group = GroupModelTest.group
        expect_str = "Тестовая группа"
        self.assertEqual(group.__str__(), expect_str)


class PostModelTest(TestCase):
    """Тест модели Post"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        User = get_user_model()

        cls.user = User.objects.create(
            username="test_user",
            password="test_password"
        )

        cls.post = Post.objects.create(
            text="Тестовая запись длиной больше 15 символов",
            author=cls.user
        )

    def test_str(self):
        """__str__ в модели совпадает с ожидаемым"""
        post = PostModelTest.post
        expect_str = "Тестовая запись"
        self.assertEqual(post.__str__(), expect_str)
