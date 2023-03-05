from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from yatube.settings import POSTS_ON_PAGE
from posts.models import Post, Group, User

POSTS_CREATED = 15


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Author")

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

    def test_index_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:index'))
        page_obj = response.context['page_obj']
        self.assertGreater(len(page_obj), 0)
        first_object = page_obj[0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)

    def test_group_list_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}
        ))
        group = response.context['group']
        page_obj = response.context['page_obj']
        self.assertGreater(len(page_obj), 0)
        post = page_obj[0]
        self.assertEqual(group, self.group)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)

    def test_profile_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.author_client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author}
        ))
        author = response.context['author']
        page_obj = response.context['page_obj']
        self.assertGreater(len(page_obj), 0)
        post = page_obj[0]
        self.assertEqual(author, self.user)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)

    def test_post_detail_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        )
        post = response.context['post']
        self.assertEqual(post, self.post)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

    def test_post_create_edit_context_form(self):
        """Сформированы формы с правильным контекстом."""
        urls = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                }
                form = response.context.get('form')
                self.assertIsInstance(form, forms.ModelForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = form.fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        is_edit = response.context['is_edit']
        post = response.context['post']
        self.assertEqual(post, self.post)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertTrue(is_edit)

    def test_post_without_group_dont_added_in_group_list(self):
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )
        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        page_obj = response.context['page_obj']
        self.assertNotIn(post, page_obj)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Author")
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        posts = [
            Post(author=cls.user,
                 text=f'{i}',
                 group=cls.group,)
            for i in range(POSTS_CREATED)
        ]
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records_index(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POSTS_ON_PAGE)

    def test_second_page_contains_five_records_index(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(
            response.context['page_obj']), (POSTS_CREATED - POSTS_ON_PAGE)
        )

    def test_first_page_contains_ten_records_group_list(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_ON_PAGE)

    def test_second_page_contains_five_records_group_list(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}) + '?page=2'
        )
        self.assertEqual(len(
            response.context['page_obj']), (POSTS_CREATED - POSTS_ON_PAGE)
        )

    def test_first_page_contains_ten_records_profile(self):
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(len(
            response.context['page_obj']), POSTS_ON_PAGE
        )

    def test_second_page_contains_five_records_profile(self):
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user}) + '?page=2')
        self.assertEqual(len(
            response.context['page_obj']), (POSTS_CREATED - POSTS_ON_PAGE)
        )
