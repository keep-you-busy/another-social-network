import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.author = User.objects.create_user(username='TestUserAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)
        self.authorized_holder = Client()
        self.authorized_holder.force_login(PostFormTests.author)
        Post.objects.all().delete()
        self.form_data = {
            'text': 'Текст формы',
            'group': self.group.pk,
        }

    def test_guest_cant_create_new_post(self):
        """Незарегистрированный пользователь не может создать пост"""
        post_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_edit_post(self):
        """Валидная форма редактирует пост и изменяет группу"""
        self.authorized_holder.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True,
        )
        new_group = Group.objects.create(
            title='Новая группа',
            slug='test-edit-slug',
        )
        new_text = Post.objects.create(
            author=self.author,
            text='Измненённый пост',
            group=new_group
        )
        form_data = {
            'text': new_text.text,
            'group': new_group.pk,
        }
        response = self.authorized_holder.post(
            reverse('posts:post_edit', kwargs={'post_id': new_group.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': new_group.pk}
            )
        )
        edit_post = Post.objects.first()
        self.assertEqual(edit_post.text, form_data['text'])
        self.assertEqual(edit_post.group.pk, form_data['group'])
        self.assertEqual(edit_post.group.pk, new_group.pk)

    def test_new_post_with_picture(self):
        """Валидная форма создаёт новый пост и отправляет изображение
        """
        Post.objects.all().delete()
        post_count = Post.objects.count()
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
            'text': 'Пост с картинкой',
            'group': self.group.pk,
            'image': uploaded
        }
        response = self.authorized_holder.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.author}
            )
        )
        self.assertTrue(
            Post.objects.filter(
                text='Пост с картинкой',
                author=self.author,
                group=self.group.pk,
            ).exists()
        )
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_authorized_client_can_comment_posts_only(self):
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.pk}),
            data={'text': 'Тестовый комментарий'},
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post.pk}
            )
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий',
            ).exists()
        )
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.pk}),
            {'text': 'Тестовый комментарий гостя'},
            follow=True
        )
        response = self.authorized_holder.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post.pk}
            )
        )
        self.assertFalse(
            Comment.objects.filter(
                text='Тестовый комментарий гостя',
            ).exists()
        )
