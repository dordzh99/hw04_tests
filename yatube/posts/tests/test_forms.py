from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Author")
        cls.user_authorized = User.objects.create_user(username="Dzhordzh")

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_authorized)

    def test_create_post_count(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}
        )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.post.author,
                text=form_data['text'],
                group=self.group,
            ).exists()
        )

    def test_post_edit_count(self):
        posts_count = Post.objects.count()
        self.assertEqual(self.post.group.id, self.post.id)
        form_data = {
            'text': 'Текст для редактирования',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post = Post.objects.latest('id')
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.id}
        )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                author=self.post.author,
                text=form_data['text'],
                group=self.group,
            ).exists()
        )

    def test_authorized_dont_edit_author_post(self):
        posts_count = Post.objects.count()
        self.assertEqual(self.post.group.id, self.post.id)
        form_data = {
            'text': 'Текст для редактирования',
            'group': self.group.id,
        }
        text1 = self.post.text
        group1 = self.post.group
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(text1, self.post.text)
        self.assertEqual(group1, self.post.group)
