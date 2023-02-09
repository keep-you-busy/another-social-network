import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.author = User.objects.create_user(username='TestUserAuthor')
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
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )
        cls.PUBLIC_TEMPLATES = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': cls.author}
            ): 'posts/profile.html',
        }
        cls.PRIVATE_TEMPLATES = {
            reverse(
                'posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.pk}
            ): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewTests.user)
        self.authorized_holder = Client()
        self.authorized_holder.force_login(PostViewTests.author)

    def check_out_context(self, context, media):
        self.assertEqual(context.text, self.post.text)
        self.assertEqual(context.group.title, self.group.title)
        self.assertEqual(context.author, self.post.author)
        self.assertEqual(context.group.pk, self.post.pk)
        self.assertEqual(media.image, self.post.image)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in {
            **self.PUBLIC_TEMPLATES, **self.PRIVATE_TEMPLATES
        }.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_holder.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_public_pages_show_correct_context(self):
        """Публичные страницы показывают верный контекст"""
        for reverse_name in self.PUBLIC_TEMPLATES:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                obj_list = response.context['page_obj'][0]
                obj_media = Post.objects.first()
                self.check_out_context(obj_list, obj_media)

    def test_post_detail_posts_show_right_context(self):
        """Шаблон поста даёт верный контекст"""
        response = self.authorized_holder.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        obj_list = response.context['post']
        obj_media = Post.objects.first()
        self.check_out_context(obj_list, obj_media)

    def test_private_pages_show_correct_context(self):
        """Приватные страницы показывают верный контекст"""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for reverse_name in self.PRIVATE_TEMPLATES:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_holder.get(
                    reverse_name, follow=True
                )
                for key, expected in form_fields.items():
                    with self.subTest(key=key):
                        obj_list = response.context['form'].fields[key]
                        self.assertIsInstance(obj_list, expected)
        response = self.authorized_holder.get(
            list(self.PRIVATE_TEMPLATES.keys())[1], follow=True
        )
        self.assertIn('is_edit', response.context)
        is_edit = response.context['is_edit']
        self.assertIsInstance(is_edit, bool)
        self.assertEqual(is_edit, True)


class CaсheTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='TestUserAuthor')
        self.guest_client = Client()
        self.post = Post.objects.create(
            author=self.author,
            text='Тестовый пост'
        )

    def test_cache_index(self):
        """Проверка хранения и очистки кэша для index."""
        index_before = self.guest_client.get(
            reverse('posts:index')
        ).content
        Post.objects.last().delete()
        index_after = self.guest_client.get(reverse('posts:index')).content
        self.assertEqual(index_before, index_after)
        cache.clear()
        index_after_clear = self.guest_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(index_before, index_after_clear)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.ADDITIONAL_POST: int = 3
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = []
        for i in range(settings.POST_VIEW + cls.ADDITIONAL_POST):
            cls.posts.append(
                Post(
                    author=cls.user,
                    text=f'Тестовый пост № {i}',
                    group=cls.group
                )
            )
        Post.objects.bulk_create(
            cls.posts,
            settings.POST_VIEW + cls.ADDITIONAL_POST
        )
        cls.PUBLIC_TEMPLATES = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': cls.user}
            ): 'posts/profile.html',
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_for_all(self):
        """Проверка первой страницы на количество постов."""
        for template in self.PUBLIC_TEMPLATES:
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POST_VIEW
                )

    def test_second_page_for_all(self):
        """Проверка второй страницы на количество постов"""
        for template in self.PUBLIC_TEMPLATES:
            with self.subTest(template=template):
                response = self.authorized_client.get(template + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.ADDITIONAL_POST
                )


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUserFollower')
        cls.author = User.objects.create_user(username='TestAuthorFollowing')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self) -> None:
        self.authorized_follower = Client()
        self.authorized_follower.force_login(FollowTest.user)
        self.authorized_following = Client()
        self.authorized_following.force_login(FollowTest.author)

    def test_follow(self):
        """Ваше описание"""
        self.authorized_follower.get(reverse(
            'posts:profile_follow',
            kwargs={
                'username':
                self.author
            }
        ))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Ваше описание"""
        self.authorized_follower.get(reverse(
            'posts:profile_follow',
            kwargs={
                'username':
                self.author
            }
        ))
        self.authorized_follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={
                'username':
                self.author
            }
        ))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_apperaing_in_feed(self):
        """Ваше описание"""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response = self.authorized_follower.get('/follow/')
        obj_list_follow = response.context['page_obj'][0].text
        self.assertEqual(obj_list_follow, self.post.text)
        response = self.authorized_following.get('/follow/')
        self.assertNotEqual(response, self.post.text)
