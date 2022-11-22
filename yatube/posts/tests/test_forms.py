import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Название тестовой группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """При отправке валидной вормы создалась новая запись в БД."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostCreateFormTests.user}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostCreateFormTests.group,
                author=PostCreateFormTests.user,
                text='Тестовый текст',
                image='posts/small.gif'
            ).exists
        )

    def test_guest_client_create_post(self):
        """Запись создаётся только после авторизации."""
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        redirect_login = (reverse('login') + '?next='
                          + reverse('posts:post_create'))
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый текст'
            ).exists()
        )
        self.assertRedirects(
            response,
            redirect_login
        )

    def test_edit_post(self):
        """При отправке валидной формы со страниц редактирования поста
        просиходит изменение поста в БД."""
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_edit = Post.objects.get(id=self.group.id)
        self.client.get(f'/posts/{post_edit.id}/edit')
        form_data = {
            'text': 'Отредактированный пост',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_edit.id}
            ),
            data=form_data,
            follow=True,
        )
        post_edit = Post.objects.get(id=self.group.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit.text, 'Отредактированный пост')

    def test_post_edit_guest_client(self):
        """Неавторизованный пользователь не может редактировать пост."""
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        redirect_login = (reverse('login') + '?next='
                          + reverse('posts:post_create'))
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый текст'
            ).exists()
        )
        self.assertRedirects(response, redirect_login)

    def test_comment_authorized_client_only(self):
        """"комментировать посты может только авторизованный
        пользователь."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий авторизованного пользователя'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Комментарий авторизованного пользователя'
            ).exists()
        )
