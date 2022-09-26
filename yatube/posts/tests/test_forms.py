import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group1 = Group.objects.create(
            title='Тестовая группа 1',
            description='Описание тестовой группы 1',
            slug='test-group-1',
        )

        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            description='Описание тестовой группы 2',
            slug='test-group-2',
        )

        cls.author1 = User.objects.create_user(username='test-author-1')

        cls.post = Post.objects.create(
            text=('Текст тестового поста'),
            author=cls.author1,
            group=cls.group1
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = PostFormTests.author1
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_for_authorized_client(self):
        '''Авторизованный пользователь может создавать пост'''
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
            'text': 'Текст нового тестового поста',
            'group': PostFormTests.group1.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse(
                                 'posts:profile',
                                 kwargs={'username': PostFormTests.author1}
                             ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Текст нового тестового поста',
                group=PostFormTests.group1,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post_for_authorized_client(self):
        '''Авторизованный пользователь может редактировать пост'''
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст тестового поста',
            'group': PostFormTests.group2.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostFormTests.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse(
                                 'posts:post_detail',
                                 kwargs={'post_id': PostFormTests.post.pk}
                             ))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Отредактированный текст тестового поста',
                group=PostFormTests.group2
            ).exists()
        )

    def test_comment_authorized_client(self):
        '''Авторизованный пользователь может добавлять комментарий'''
        post = Post.objects.latest('pub_date')
        comments_count = post.comments.count()
        form_data = {'text': 'Тестовый комментарий', }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse(
                                 'posts:post_detail',
                                 kwargs={'post_id': post.pk}
                             ))
        self.assertEqual(post.comments.count(), comments_count + 1)
        self.assertTrue(
            post.comments.filter(
                text='Тестовый комментарий',
                author=PostFormTests.author1
            ).exists())

        post_detail_response = self.guest_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': post.pk})
        )
        self.assertEqual(
            'Тестовый комментарий',
            post_detail_response.context['comments'][0].text
        )

    def test_comment_guest_client(self):
        '''Невторизованный пользователь не может добавлять комментарий'''
        post = Post.objects.latest('pub_date')
        comments_count = post.comments.count()
        form_data = {'text': 'Тестовый комментарий 2', }
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{post.pk}/comment/')
        self.assertEqual(post.comments.count(), comments_count)
        self.assertFalse(
            Comment.objects.filter(
                text='Тестовый комментарий 2'
            ).exists())
