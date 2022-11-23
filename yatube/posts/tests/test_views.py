import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()
ten_posts = 10
three_posts = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='test_user',
        )
        cls.group = Group.objects.create(
            title='Название',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.posts = [
            Post(
                author=cls.author,
                group=cls.group,
                text='Тестовый текст',
                image=cls.uploaded,
            )
            for i in range(13)
        ]
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует корректный шаблон."""
        templates_pages_names = {
            reverse('posts:index'): ('posts/index.html'),
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ): ('posts/group_list.html'),
            reverse(
                'posts:profile', kwargs={'username': 'test_user'}
            ): ('posts/profile.html'),
            reverse(
                'posts:post_detail', kwargs={'post_id': '1'}
            ): ('posts/post_detail.html'),
            reverse(
                'posts:post_edit', kwargs={'post_id': '1'}
            ): ('posts/post_create.html'),
            reverse('posts:post_create'): ('posts/post_create.html'),
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Шаблоне index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author.username
        group_title = first_object.group.title
        self.assertEqual(post_text, 'Тестовый текст')
        self.assertEqual(post_author, 'test_user')
        self.assertEqual(group_title, 'Название')
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_list_page_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        first_object = response.context['page_obj'][0]
        group_title = first_object.group.title
        group_description = first_object.group.description
        group_slug = first_object.group.slug
        self.assertEqual(group_title, 'Название')
        self.assertEqual(group_description, 'Тестовое описание')
        self.assertEqual(group_slug, 'test-slug')
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'test_user'})
        )
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author.username
        self.assertEqual(post_author, 'test_user')
        self.assertEqual(post_text, 'Тестовый текст')

    def test_post_detail_page_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': 1})
        )
        first_object = response.context['post']
        post_text = first_object.text
        post_author = first_object.author.username
        group_title = first_object.group.title
        self.assertEqual(post_text, 'Тестовый текст')
        self.assertEqual(post_author, 'test_user')
        self.assertEqual(group_title, 'Название')

    def test_edit_post_page_shows_correct_context(self):
        """Шаблон редактирования post_create сформирован
        с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': 1})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_shows_correct_context(self):
        """Шаблон создания поста post_create сформирован
        с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_index_group_list_profile_pages(self):
        """Созданный пост отобразился на главной странице, на странице группы и
        в профиле пользователя."""
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'test_user'}),
        )
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertEqual(len(response.context['page_obj'].object_list), 10)

    def test_post_not_in_wrong_group(self):
        """Пост не попал в группу, для которой не был предназначен."""
        wrong_group = Group.objects.create(
            title='Ошибочная тестовая группа',
            slug='test-wrong-slug',
            description='Тестовое описание ошибочной группы',
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': wrong_group.slug})
        )
        first_object = response.context['page_obj']
        self.assertEqual(len(first_object), 0)

    def test_group_post_pages(self):
        """Пост появился на главной странице, в группе и профиле автора."""
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.author.username}
            ),
        )
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertEqual(len(response.context['page_obj'].object_list), 10)

    def test_paginator(self):
        """На первой странице index, profile, group_list 10 постов,
        на второй странице 3 поста."""
        pages = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}),
            reverse('posts:profile',
                    kwargs={'username': 'test_user'})
        )
        page_numbers = {ten_posts: 1,
                        three_posts: 2}
        for posts, page_number in page_numbers.items():
            for page in pages:
                response = self.client.get(page, {'page': page_number})
                amount_of_posts = len(
                    response.context.get('page_obj').object_list
                )
            self.assertEqual(amount_of_posts, posts)

    def test_cache_index(self):
        """Тест кеширования главной страницы."""
        first_object = self.authorized_client.get(reverse('posts:index'))
        post = Post.objects.get(id=1)
        post.text = 'Изменённый текст'
        post.save()
        second_object = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_object.content, second_object.content)
        cache.clear()
        third_object = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_object.content, third_object.content)


class FollowingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='test_user',
        )
        cls.follower = User.objects.create(
            username='test_follower',
        )
        cls.author = User.objects.create(
            username='test_author',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )

    def setUp(self):
        self.authorized_client_unfollower = Client()
        self.authorized_client_unfollower.force_login(FollowingTests.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(FollowingTests.author)
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(FollowingTests.follower)
        cache.clear()

    def test_users_follow(self):
        """Авторизованный пользовательно может подписываться
        на других пользователей."""
        followers_now = Follow.objects.filter(
            author=FollowingTests.author
        ).count()
        self.authorized_client_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author})
        )
        followers_after = Follow.objects.filter(author=self.author).count()
        self.assertEqual(followers_now + 1, followers_after)

    def test_users_unfollow(self):
        """Авторизованный пользователь может отписываться
        от других пользователей."""
        followers_now = Follow.objects.filter(author=self.author).count()
        self.authorized_client_follower.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.follower})
        )
        followers_after = Follow.objects.filter(author=self.author).count()
        self.assertEqual(followers_now, followers_after)

    def test_users_see_following_posts(self):
        """Новая запись появляется в ленте у подписчиков."""
        self.authorized_client_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author})
        )
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        posts_before = len(response.context['page_obj'])
        Post.objects.create(
            text='Новый текст',
            author=FollowingTests.author,
        )
        response_1 = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        posts_after = len(response_1.context['page_obj'])
        self.assertEqual(posts_before + 1, posts_after)

    def test_not_followers_dont_see_authors_posts(self):
        """Посты пользователя не появляются в ленте у пользователей,
        которые на них не подписаны."""
        response = self.authorized_client_unfollower.get(
            reverse('posts:follow_index')
        )
        posts_before = len(response.context['page_obj'])
        Post.objects.create(
            text='Новый текст',
            author=FollowingTests.author,
        )
        response_1 = self.authorized_client_unfollower.get(
            reverse('posts:follow_index')
        )
        posts_after = len(response_1.context['page_obj'])
        self.assertEqual(posts_before, posts_after)
