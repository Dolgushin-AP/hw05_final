from math import ceil

from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from ..forms import PostForm
from ..models import Group, Post, User, Follow


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_follower = User.objects.create_user(
            username='Follower'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
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
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Тестовый пост',
            image=cls.uploaded,
        )
        Follow.objects.create(
            author=cls.user,
            user=cls.user_follower
        )
        cls.index_url = ('posts:index', None, 'posts/index.html')
        cls.group_url = (
            'posts:group_list',
            (cls.group.slug,),
            'posts/group_list.html'
        )
        cls.profile_url = (
            'posts:profile',
            (cls.post.author,),
            'posts/profile.html'
        )
        cls.post_detail_url = (
            'posts:post_detail',
            (cls.post.pk,),
            'posts/post_detail.html'
        )
        cls.post_edit_url = (
            'posts:post_edit',
            (cls.post.pk,),
            'posts/create_post.html'
        )
        cls.create_post_url = (
            'posts:post_create',
            None,
            'posts/create_post.html'
        )
        cls.urls_all = (
            cls.index_url,
            cls.group_url,
            cls.profile_url,
            cls.post_detail_url,
            cls.post_edit_url,
            cls.create_post_url
        )
        cls.profile_follow_url = (
            'posts:profile_follow',
            (cls.user,),
            None
        )
        cls.profile_unfollow_url = (
            'posts:profile_unfollow',
            (cls.user,),
            None
        )
        cls.follow_index_url = ('posts:follow_index', None, None)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_all_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url_name, args, template in self.urls_all:
            with self.subTest(url_name=template):
                response = self.authorized_client.get(
                    reverse(url_name, args=args)
                )
                self.assertTemplateUsed(response, template)

    def custom_checking_func(self, first_object):
        self.assertEqual(first_object.author.username, self.user.username)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        name, _, _ = self.index_url
        response = self.authorized_client.get(reverse(name))
        self.assertIn('page_obj', response.context, msg='присутствует')
        self.assertGreaterEqual(len(response.context['page_obj']), 1)
        first_object = response.context['page_obj'][0]
        self.custom_checking_func(first_object)

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        name, args, _ = self.group_url
        response = self.authorized_client.get(reverse(name, args=args))
        self.assertIn('page_obj', response.context, msg='присутствует')
        self.assertGreaterEqual(len(response.context['page_obj']), 1)
        first_object = response.context['page_obj'][0]
        self.custom_checking_func(first_object)
        self.assertEqual(
            response.context.get('group'), self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        name, args, _ = self.profile_url
        response = self.authorized_client.get(reverse(name, args=args))
        self.assertIn('page_obj', response.context, msg='присутствует')
        self.assertGreaterEqual(len(response.context['page_obj']), 1)
        first_object = response.context['page_obj'][0]
        self.custom_checking_func(first_object)
        self.assertEqual(
            response.context.get('author'), self.post.author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        name, args, _ = self.post_detail_url
        response = self.authorized_client.get(reverse(name, args=args))
        first_object = response.context['post']
        self.custom_checking_func(first_object)

    def test_create_post_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        name, args, _ = self.create_post_url
        response = self.authorized_client.get(reverse(name, args=args))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        name, args, _ = self.post_edit_url
        response = self.authorized_client.get(reverse(name, args=args))
        self.assertTrue(response.context.get('is_edit'))
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context.get('form').instance, self.post)

    def test_cache_context(self):
        """index - кэш сохранён"""
        name, _, _ = self.index_url
        base_data = self.authorized_client.get(
            reverse(name)
        ).content
        Post.objects.filter(id=self.post.id).delete()
        renew_data = self.authorized_client.get(
            reverse(name)
        ).content
        self.assertEqual(renew_data, base_data)
        cache.clear()
        wiped_data = self.authorized_client.get(
            reverse(name)
        ).content
        self.assertNotEqual(renew_data, wiped_data)

    def test_authorized_user_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей"""
        name, args, _ = self.profile_follow_url
        self.authorized_client.force_login(self.user_follower)
        response = self.authorized_client.get(
            reverse(name, args=args),
            follow=True)
        name, args, _ = self.profile_url
        self.assertRedirects(response, reverse(name, args=args))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_follower, author=self.user
            ).exists()
        )

    def test_authorized_user_unfollow(self):
        """Авторизованный пользователь может отписываться
        от других пользователей"""
        name, args, _ = self.profile_unfollow_url
        self.authorized_client.force_login(self.user_follower)
        response = self.authorized_client.get(
            reverse(name, args=args),
            follow=True)
        name, args, _ = self.profile_url
        self.assertRedirects(response, reverse(name, args=args))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower, author=self.user
            ).exists()
        )

    def test_new_post_in_page_follower_only(self):
        """Новая запись пользователя появляется в ленте
        его подписчиков"""
        name, _, _ = self.follow_index_url
        response = self.authorized_client.get(reverse(name))
        first_object = response.context['page_obj']
        self.assertNotIn(self.post, first_object)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='noname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        cls.ALL_POSTS = 13
        Post.objects.bulk_create(
            [Post(author=cls.user, text=f"Тестовый пост {i}", group=cls.group)
                for i in range(cls.ALL_POSTS)]
        )

    def setUp(self):
        self.guest_client = Client()
        self.pagin_urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )

    def test_first_page_contains_ten_records(self):
        """Проверка пагинатора. 10 записей на первой странице"""
        for url in self.pagin_urls:
            response = self.guest_client.get(url)
            self.assertEqual(
                len(response.context['page_obj']),
                settings.POSTS_PER_PAGE
            )

    def test_second_page_contains_three_records(self):
        """Проверка пагинатора. 3 записи на второй странице"""
        page_number = ceil(self.ALL_POSTS / settings.POSTS_PER_PAGE)
        for url in self.pagin_urls:
            response = self.guest_client.get(
                url + '?page=' + str(page_number)
            )
            self.assertEqual(
                len(response.context['page_obj']),
                (self.ALL_POSTS - (
                    page_number - 1
                ) * settings.POSTS_PER_PAGE)
            )
