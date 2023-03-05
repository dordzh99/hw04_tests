from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()

LEN_POSTS = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Author")
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = PostModelTest.post
        post_text = post.text[:LEN_POSTS]
        self.assertEqual(str(post), post_text)

    def test_models_have_correct_object_names_group(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = PostModelTest.group
        self.assertEqual(str(group), group.title)

    def test_verbose_name(self):
        field_verboses = {
            'text': 'Пост',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        field_help_texts = {
            'text': 'Текст нового поста',
            'pub_date': 'Здесь действующая дата',
            'author': 'Создатель поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).help_text, expected_value
                )
