import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..views import POSTS_ON_PAGE
from ..models import Post, Group, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


def last_page_parameters(posts_total):
    posts_on_last_page = posts_total % POSTS_ON_PAGE
    if posts_on_last_page < POSTS_ON_PAGE:
        last_page_num = posts_total // POSTS_ON_PAGE + 1
    else:
        last_page_num = posts_total // POSTS_ON_PAGE
    return last_page_num, posts_on_last_page


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group1 = Group.objects.create(
            title='Заголовок тестовой группы 1',
            description='Описание тестовой группы 1',
            slug='test-group-1',
        )

        cls.group2 = Group.objects.create(
            title='Заголовок тестовой группы 2',
            description='Описание тестовой группы 2',
            slug='test-group-2',
        )

        cls.author1 = User.objects.create_user(username='test-author-1')
        cls.author2 = User.objects.create_user(username='test-author-2')

        for _ in range(9):

            Post.objects.create(
                text=('Текст поста: автор 1, группа 1'),
                author=cls.author1,
                group=cls.group1
            )

            Post.objects.create(
                text=('Текст поста: автор 2, группа 2'),
                author=cls.author2,
                group=cls.group2
            )

            Post.objects.create(
                text=('Текст поста: автор 2, группа 1'),
                author=cls.author2,
                group=cls.group1
            )

            Post.objects.create(
                text=('Текст поста: автор 1, без группы'),
                author=cls.author2,
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = PostViewsTests.author1
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

        # тестируем доступность url
    def test_pages_use_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': PostViewsTests.group1.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': PostViewsTests.author1.username}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': Post.objects.last().pk}
                    ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': Post.objects.last().pk}
                    ): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/index.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Тестируем контексты страниц

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_post_on_page = response.context['page_obj'][0]
        latest_post_created = Post.objects.latest('pub_date')
        self.assertEqual(first_post_on_page.pk, latest_post_created.pk)
        self.assertEqual(first_post_on_page.text, latest_post_created.text)
        self.assertEqual(first_post_on_page.author, latest_post_created.author)
        self.assertEqual(first_post_on_page.group, latest_post_created.group)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostViewsTests.group2.slug})
        )
        test_group = response.context['group']
        number_of_group_posts = len(response.context['page_obj'])
        first_post_on_page = response.context['page_obj'][0]
        group_posts_list = Post.objects.filter(group=PostViewsTests.group2)
        latest_post_created = group_posts_list.latest('pub_date')
        self.assertEqual(test_group, PostViewsTests.group2)
        self.assertEqual(number_of_group_posts, group_posts_list.count())
        self.assertEqual(first_post_on_page.pk, latest_post_created.pk)
        self.assertEqual(first_post_on_page.text, latest_post_created.text)
        self.assertEqual(first_post_on_page.group, latest_post_created.group)
        self.assertEqual(first_post_on_page.author, latest_post_created.author)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostViewsTests.author1})
        )
        test_author = response.context['username']
        number_of_author_posts = len(response.context['page_obj'])
        first_post_on_page = response.context['page_obj'][0]
        author_posts_list = Post.objects.filter(author=PostViewsTests.author1)
        latest_post_created = author_posts_list.latest('pub_date')
        self.assertEqual(test_author, PostViewsTests.author1)
        self.assertEqual(number_of_author_posts, author_posts_list.count())
        self.assertEqual(first_post_on_page.pk, latest_post_created.pk)
        self.assertEqual(first_post_on_page.text, latest_post_created.text)
        self.assertEqual(first_post_on_page.group, latest_post_created.group)
        self.assertEqual(first_post_on_page.author, latest_post_created.author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': Post.objects.last().pk})
        )
        test_post = response.context['post']
        post_from_db = Post.objects.last()
        self.assertEqual(test_post.author, post_from_db.author)
        self.assertEqual(test_post.text, post_from_db.text)
        self.assertEqual(test_post.group, post_from_db.group)

    def test_post_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом
            при создании нового поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом
            при редактировании поста."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': Post.objects.last().pk})
        )
        test_post = response.context['post']
        post_from_db = Post.objects.last()
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        self.assertEqual(test_post.author, post_from_db.author)
        self.assertEqual(test_post.text, post_from_db.text)
        self.assertEqual(test_post.group, post_from_db.group)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_belongs_to_right_pages(self):
        '''Создаваемый пост попадает на страницы индекса, нужной группы,
            в профайл автора и не попадает на страницу другой группы'''
        test_post = Post.objects.create(
            text=('Это пост для проверки принадлежности к группам'),
            author=PostViewsTests.author1,
            group=PostViewsTests.group2
        )
        index_response = self.authorized_client.get(reverse('posts:index'))
        group_response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostViewsTests.group2.slug})
        )
        profile_response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostViewsTests.author1})
        )
        wrong_group_response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostViewsTests.group1.slug})
        )
        self.assertIn(test_post, index_response.context['page_obj'])
        self.assertIn(test_post, group_response.context['page_obj'])
        self.assertIn(test_post, profile_response.context['page_obj'])
        self.assertNotIn(test_post, wrong_group_response.context['page_obj'])

    def test_image_in_post_gets_to_all_pages(self):
        '''Картинка из поста корректно отображается на страницах
            index, profile, group_list'''
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
        post_with_image = Post.objects.create(
            text=('Это пост для проверки наличия картинки в индексе'),
            author=PostViewsTests.author1,
            group=PostViewsTests.group2,
            image=uploaded
        )
        response_dict = {
            'index_response': self.authorized_client.get(
                reverse('posts:index')),
            'group_response': self.authorized_client.get(
                reverse('posts:group_posts',
                        kwargs={'slug': PostViewsTests.group2.slug})),
            'profile_response': self.authorized_client.get(
                reverse('posts:profile',
                        kwargs={'username': PostViewsTests.author1})),
        }
        for value in response_dict.values():
            with self.subTest(value=value):
                self.assertEqual('posts/small.gif',
                                 value.context['page_obj'][0].image)
        post_detail_response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': post_with_image.pk}))
        self.assertEqual('posts/small.gif',
                         post_detail_response.context['post'].image)

    def test_profile_follow(self):
        '''Авторизованный пользователь создает подписку на автора'''
        user = PostViewsTests.author1
        author = PostViewsTests.author2
        Follow.objects.create(user=user, author=author)
        self.assertTrue(
            Follow.objects.filter(user=user, author=author).exists()
        )
# Тестируем паджинатор

    def test_index_first_page_amount_of_posts(self):
        '''Первая страница index содержит заданное количество постов'''
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POSTS_ON_PAGE)

    def test_index_last_page_amount_of_posts(self):
        '''Последняя страница index содержит остаток постов'''
        (last_page_num,
         posts_on_last_page) = last_page_parameters(Post.objects.count())
        response = self.client.get(reverse('posts:index')
                                   + '?page=' + str(last_page_num))
        self.assertEqual(len(response.context['page_obj']), posts_on_last_page)

    def test_group_list_first_page_amount_of_posts(self):
        '''Первая страница group_list содержит заданное количество постов'''
        response = self.client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostViewsTests.group1.slug})
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_ON_PAGE)

    def test_group_list_last_page_amount_of_posts(self):
        '''Последняя страница group_list содержит остаток постов'''
        (last_page_num,
         posts_on_last_page) = last_page_parameters(
            Post.objects.filter(group=PostViewsTests.group1).count())
        response = self.client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostViewsTests.group1.slug}
                    ) + '?page=' + str(last_page_num))
        self.assertEqual(len(response.context['page_obj']), posts_on_last_page)

    def test_profile_first_page_amount_of_posts(self):
        '''Первая страница profile содержит заданное количество постов'''
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': PostViewsTests.author2.username}))
        self.assertEqual(len(response.context['page_obj']), POSTS_ON_PAGE)

    def test_profile_last_page_amount_of_posts(self):
        '''Последняя страница group_list содержит остаток постов'''
        (last_page_num,
         posts_on_last_page) = last_page_parameters(
            Post.objects.filter(author=PostViewsTests.author2).count())
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': PostViewsTests.author2}
                    ) + '?page=' + str(last_page_num))
        self.assertEqual(len(response.context['page_obj']), posts_on_last_page)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.author1,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        posts_old = response_old.content
        self.assertEqual(posts_old, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        posts_new = response_new.content
        self.assertNotEqual(posts_old, posts_new)
