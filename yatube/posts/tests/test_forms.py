from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


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
        self.client.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_authorized)

    def test_create_post_count(self):
        Post.objects.all().delete()
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.id,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}
        )
        )
        self.assertEqual(Post.objects.count(), 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text=form_data['text'],
                group=self.group,
            ).exists()
        )

    def test_post_edit_count(self):
        group = Group.objects.create(
            slug='post_edit_group',
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст для редактирования',
            'group': group.id,
        }
        response = self.client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post = group.publications.last()
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.id}
        )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.text, form_data['text'])

    def test_authorized_dont_edit_author_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст для редактирования',
            'group': self.group.id,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        edited_post = Post.objects.get(id=self.post.id)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(edited_post.text, self.post.text)
        self.assertEqual(edited_post.group, self.post.group)
