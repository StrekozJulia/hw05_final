from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )

        cls.author1 = User.objects.create_user(username='test-author')
        cls.author2 = User.objects.create_user(username='HasNoName')

        cls.post1 = Post.objects.create(
            text='тестовый текст',
            author=cls.author1,
        )

        cls.post2 = Post.objects.create(
            text='тестовый текст 2',
            author=cls.author2,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostURLTests.author2
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_nonauth_urls_exist_at_desired_locations(self):
        '''Страницы доступны для неавторизованных пользователей'''
        url_list = [
            '/',
            f'/group/{PostURLTests.group.slug}/',
            f'/profile/{PostURLTests.author2.username}/',
            f'/posts/{PostURLTests.post1.pk}/',
        ]
        for url in url_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        '''Несуществующая страница'''
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_exists_at_desired_location(self):
        '''Страница /create/ доступна только авторизованным пользователям'''
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_exists_at_desired_location(self):
        '''Страница /posts/<post_id>/edit/ доступна только автору'''
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post2.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_anonymous(self):
        '''Страница /create/ перенаправляет анонимного пользователя
            на форму регистрации'''
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_url_redirect_anonymous(self):
        '''Страница /edit/ перенаправляет анонимного пользователя
            на форму регистрации'''
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post1.pk}/edit/', follow=True)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostURLTests.post1.pk}/edit/')

    def test_edit_url_redirect_not_author(self):
        '''Страница /posts/<post_id>/edit/ перенаправляет не автора
            на страницу поста'''
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post1.pk}/edit/',
            follow=True)
        self.assertRedirects(response, f'/posts/{PostURLTests.post1.pk}/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.author2.username}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post1.pk}/': 'posts/post_detail.html',
            f'/posts/{PostURLTests.post2.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
