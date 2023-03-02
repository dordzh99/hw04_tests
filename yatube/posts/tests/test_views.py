from django.contrib.auth import get_user_model
from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from yatube.settings import POSTS_ON_PAGE
from posts.models import Post, Group

User = get_user_model()

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

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            )): 'posts/group_list.html',
            (reverse(
                'posts:profile', kwargs={'username': self.post.author}
            )): 'posts/profile.html',
            (reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )): 'posts/post_detail.html',
            (reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            )): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_group_0, self.post.group)

    def test_group_list_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}
        ))
        group = response.context['group']
        page_obj = response.context['page_obj']
        self.assertIsInstance(page_obj, Page)
        self.assertGreater(len(page_obj), 0)
        post = page_obj[0]
        post_author_0 = post.author
        post_text_0 = post.text
        post_group_0 = post.group
        self.assertEqual(group, self.group)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_group_0, self.post.group)

    def test_profile_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.author_client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author}
        ))
        author = response.context['author']
        page_obj = response.context['page_obj']
        self.assertIsInstance(page_obj, Page)
        self.assertGreater(len(page_obj), 0)
        post = page_obj[0]
        post_author_0 = post.author
        post_text_0 = post.text
        post_group_0 = post.group
        self.assertEqual(author, self.user)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_group_0, self.post.group)

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
        """Сформированы формы правильным контекстом."""
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

        for i in range(POSTS_CREATED):
            Post.objects.create(author=cls.user,
                                text=f'{i}',
                                group=cls.group,
                                )

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
