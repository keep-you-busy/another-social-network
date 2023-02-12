from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostUrlTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.PUBLIC_URLS = {
            '/': (
                'posts/index.html', HTTPStatus.OK
            ),
            f'/group/{cls.group.slug}/': (
                'posts/group_list.html', HTTPStatus.OK
            ),
            f'/profile/{cls.post.author}/': (
                'posts/profile.html', HTTPStatus.OK
            ),
            f'/posts/{cls.post.pk}/': (
                'posts/post_detail.html', HTTPStatus.OK
            ),
            '/unexisting_page/': (
                'core/404.html', HTTPStatus.NOT_FOUND
            ),
        }
        cls.PRIVATE_URLS = {
            '/create/': (
                'posts/create_post.html', HTTPStatus.OK
            ),
            f'/posts/{cls.post.pk}/edit/': (
                'posts/create_post.html', HTTPStatus.OK
            ),
            '/follow/': (
                'posts/follow.html', HTTPStatus.OK
            ),
        }
        cls.PRIVATE_URLS_REDIRECT = {
            f'/posts/{cls.post.pk}/edit/':
                f'/posts/{cls.post.pk}/',
            f'/posts/{cls.post.pk}/comment/':
                f'/posts/{cls.post.pk}/',
            f'/profile/{cls.post.author}/follow/':
                f'/profile/{cls.post.author}/',
            f'/profile/{cls.post.author}/unfollow/':
                f'/profile/{cls.post.author}/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostUrlTests.user)
        self.authorized_holder = Client()
        self.authorized_holder.force_login(PostUrlTests.author)

    def test_url_public_exists_at_desired_location(self):
        """Публичный URL-адрес доступен любому пользователю."""
        for url, status in self.PUBLIC_URLS.items():
            with self.subTest(url=url):
                if type(status) is tuple:
                    response = self.guest_client.get(url)
                    self.assertEqual(response.status_code, status[1])

    def test_url_private_exists_at_desired_location(self):
        """Приватный URL-адрес доступен зарегистрированному пользователю."""
        for url, status in self.PRIVATE_URLS.items():
            with self.subTest(url=url):
                if type(status) is tuple:
                    response = self.authorized_holder.get(url)
                    self.assertEqual(response.status_code, status[1])

    def test_url_make_right_redirect(self):
        """Ваше описание"""
        for url, redirect in self.PRIVATE_URLS_REDIRECT.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_post_create_redirect(self):
        """Страница создания поста перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_urls_uses_correct_template(self):
        """Url-страница использует верный шаблон"""
        for url, template in {**self.PUBLIC_URLS, **self.PRIVATE_URLS}.items():
            with self.subTest(url=url):
                if template[0] is not None:
                    response = self.authorized_holder.get(url)
                    self.assertTemplateUsed(response, template[0])
