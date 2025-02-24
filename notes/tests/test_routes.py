from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):
    """
    Класс тестов, унаследованный от TestCase.

    Проверяет редиректы, коды ответа,
    тестирует доступ для авторизированных
    или анонимных пользователей.
    """

    @classmethod
    def setUpTestData(cls):
        """Инициализация тестовых данных."""
        # Автор
        cls.author = User.objects.create(username='Джоанн Роулинг')
        # Заметка
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Какой-то текст.',
            author=cls.author
        )
        # Читатель
        cls.reader = User.objects.create(username='Читатель')
        # Создаем клиент автора
        cls.author_client = Client()
        # Логиним клиент автора
        cls.author_client.force_login(cls.author)
        # Создаем клиент читателя
        cls.reader_client = Client()
        # Логиним читателя
        cls.reader_client.force_login(cls.reader)

        # URLs для доступа анонимных пользователей
        cls.urls_for_anonymous = (
            reverse('notes:home'),
            reverse('users:login'),
            reverse('users:logout'),
            reverse('users:signup'),
        )
        # URLs для доступа автора заметки
        cls.urls_for_author = (
            reverse('notes:add'),
            reverse('notes:list'),
            reverse('notes:success'),
        )
        # URLs для доступа исключително автора заметки
        cls.urls_for_only_author = (
            reverse('notes:detail', args=(cls.note.slug,)),
            reverse('notes:edit', args=(cls.note.slug,)),
            reverse('notes:delete', args=(cls.note.slug,)),
        )
        # URL для страницы с логином
        cls.login_url = reverse('users:login')

    def test_pages_availability(self):
        """
        Тест для /home, /login, /logout, /signup.

        Проверка доступа главной страницы для анонимного пользователя;
        страницы регистрации, страниц входа и выхода для всех пользователей.
        """
        for url in self.urls_for_anonymous:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_note_add_and_list_for_auth_user(self):
        """
        Тест для notes/, done/, add/.

        Проверка доступа аутентифицированному пользователю страницы
        со списком заметок, страницы успешного добавления заметки и
        страницы добавления новой заметки
        """
        for url in self.urls_for_author:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_detail_edit_and_delete_for_only_author(self):
        """
        Тест для /detail, /edit, /delete.

        Проверка доступа страницы заметки, страницы редактирования заметки и
        страницы удаления заметки только автору.
        """
        user_status = (
            (self.author_client, HTTPStatus.OK),
            (self.reader_client, HTTPStatus.NOT_FOUND),
        )
        for user, status in user_status:
            for url in self.urls_for_only_author:
                with self.subTest(user=user, url=url):
                    response = user.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        Тест для редиректа анонимного пользователя.

        Проверка, что при попытке перехода на страницу списка заметок,
        страницу успешного добавления записи, страницу добавления заметки,
        отдельной заметки, редактирования или удаления заметки анонимный
        пользователь редиректится на страницу логина.
        """
        urls = self.urls_for_only_author + self.urls_for_author
        for url in urls:
            with self.subTest(url=url):
                redirect_url = f'{self.login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
