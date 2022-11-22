from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текстовый пост',
        )

    def test_model_post_has_correct_object_names(self):
        """Проверяем, что у модели post корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_model_group_has_correct_object_names(self):
        """Проверяем, что у модели group корректно работает __str__."""
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def text_verbose_name(self):
        """Проверяем, что verbose_name совпадает с ожидаемым."""
        post = PostModelTest.post
        verbose_fields = {
            'author': 'Автор',
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'group': 'Группа',
        }
        for field, expected_value in verbose_fields.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        """Проверяем, что help_text совпадает с ожидаемым."""
        post = PostModelTest.post
        help_text_fields = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Картинка',
        }
        for field, expected_value in help_text_fields.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
