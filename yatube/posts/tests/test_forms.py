import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.post_edit_url = ('posts:post_edit', (cls.post.id,))
        cls.create_post_url = ('posts:post_create', None)
        cls.user_login_url = ('users:login', None)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        setting_list = set(Post.objects.values_list('id', flat=True))
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
            'group': self.group.id,
            'text': 'Тестовый пост',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse(self.create_post_url[0]),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text='Тестовый пост',
                author=self.user,
            ).exists()
        )
        new_posts = set(Post.objects.values_list('id', flat=True))
        new_posts_ids = new_posts(setting_list)
        self.assertEqual(len(new_posts_ids), 1)
        post_create = Post.objects.latest('id')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_create.text, form_data['text'])
        self.assertEqual(post_create.author, self.user)
        self.assertEqual(post_create.group.id, form_data['group'])
        self.assertEqual(post_create.image, form_data['image'])

    def test_post_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.pk,
            'text': 'Тестовый пост',
        }
        name, args = self.post_edit_url
        response = self.authorized_client.post(
            reverse(name, args=args),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                text='Тестовый пост',
                author=self.user,
            ).exists()
        )
        post_post_edit = Post.objects.latest('id')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_post_edit.text, form_data['text'])
        self.assertEqual(post_post_edit.author, self.user)
        self.assertEqual(post_post_edit.group.id, form_data['group'])

    def test_create_post(self):
        """Неавторизованный пользователь не отправит форму записи в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
        }
        name, args = self.create_post_url
        response = self.guest_client.post(
            reverse(name, args=args),
            data=form_data,
            follow=True,
        )
        create = reverse(name, args=args)
        name, args = self.user_login_url
        login = reverse(name, args=args)
        self.assertRedirects(response, f'{login}?next={create}')
        self.assertEqual(Post.objects.count(), posts_count)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый титул',
            slug='slug_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user
        )
        cls.comment = Comment.objects.create(
            post_id=cls.post.id,
            author=cls.user,
            text='Комментарий к публикации',
        )
        cls.add_comment_url = ('posts:add_comment', (cls.post.id,))
        cls.post_detail_url = ('posts:post_detail', (cls.post.id,))

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Валидная форма создает комментарий."""
        setting_list = set(Comment.objects.values_list('id', flat=True))
        form_data = {'text': 'Тест комментария',
                     }
        name, args = self.add_comment_url
        response = self.authorized_client.post(
            reverse(name, args=args),
            data=form_data,
            follow=True,
        )
        name, args = self.post_detail_url
        self.assertRedirects(
            response,
            reverse(name, args=args)
        )
        new_comments = set(
            Comment.objects.values_list('id',
                                        flat=True
                                        )
        )
        new_posts_ids = new_comments.difference(setting_list)
        self.assertEqual(len(new_posts_ids), 1)
        post = Comment.objects.get(id=new_posts_ids.pop())
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(self.user, post.author)
        self.assertEqual(self.post.id, post.post.id)
