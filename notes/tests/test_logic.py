from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()
URL_TO_DONE = reverse('notes:success')
URL_TO_ADD = reverse('notes:add')
URL_TO_LOGIN = reverse('users:login')


class TestNoteCreation(TestCase):
    """
    Класс тестов, унаследованный от TestCase.

    Проверки:
    - Авторизированный пользователь может создать заметку,
    а анонимный нет;
    - Невозможно создать две заметки с одинаковым slug;
    - Если при создании заметки не заполнен slug, то он
    формируется автоматически с помощью slugify;
    """

    NOTE_TITLE = 'Заголовок заметки.'
    NOTE_TEXT = 'Текст заметки.'
    NOTE_SLUG = 'slug'

    @classmethod
    def setUpTestData(cls):
        """Инициализация тестовых данных."""
        # Пользователь
        cls.user = User.objects.create(username='Гарри Поттер')
        # Создаем клиент пользователя
        cls.auth_client = Client()
        # Логиним клиент пользователя
        cls.auth_client.force_login(cls.user)
        # Данные для POST-запроса при создании заметки
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG
        }

        cls.add = reverse('notes:add')

    def setUp(self):
        """Очищает БД в начале каждого теста."""
        Note.objects.all().delete()

    def test_auth_user_can_create_note(self):
        """Авторизированный пользователь может создать заметку."""
        # Выполняем POST-запрос через авторизированный клиент
        response = self.auth_client.post(URL_TO_ADD, data=self.form_data)
        self.assertRedirects(response, URL_TO_DONE)
        self.assertEqual(Note.objects.count(), 1)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        response = self.client.post(URL_TO_ADD, data=self.form_data)
        self.assertRedirects(response, f'{URL_TO_LOGIN}?next={URL_TO_ADD}')
        self.assertEqual(Note.objects.count(), 0)

    def test_empty_slug(self):
        """
        Проверка отсутствия slug.

        Если отсутствует slug - автоматически создать новый
        на основе заголовка.
        """
        # Убираем slug из данных
        self.form_data.pop('slug')
        self.form_data['title'] = 'Тестовый заголовок! @#'
        # Выполняем запрос на создание заметки без slug
        response = self.auth_client.post(URL_TO_ADD, data=self.form_data)
        # Проверяем редирект
        self.assertRedirects(response, URL_TO_DONE)
        # Проверяем правильность slug
        new_note = Note.objects.latest('id')
        expected_slug = slugify('Тестовый заголовок! @#')
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    """
    Класс тестов, унаследованный от TestCase.

    Проверки:
    - Пользователь может редактировать и удалять свои заметки,
    но не может редактировать и удалять чужие;
    - Невозможно создать две заметки с одинаковым slug.
    """

    NOTE_TITLE = 'Заголовок заметки.'
    NOTE_TEXT = 'Текст заметки.'
    NOTE_SLUG = 'slug'
    UPDATE_NOTE_TITLE = 'Обновленный заголовок'
    UPDATE_NOTE_TEXT = 'Обновленный текст.'
    UPDATE_NOTE_SLUG = 'update_slug'

    @classmethod
    def setUpTestData(cls):
        """Инициализация тестовых данных."""
        # Автор
        cls.author = User.objects.create(username='Джоанн Роулинг')
        # Заметка
        cls.note = Note.objects.create(
            title='Заголовок',
            text=cls.NOTE_TEXT,
            slug='Slug',
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
        # Создаем данные формы
        cls.form_data = {
            'title': cls.UPDATE_NOTE_TITLE,
            'text': cls.UPDATE_NOTE_TEXT,
            'slug': cls.UPDATE_NOTE_SLUG
        }
        # URL для редактирования заметки
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        # URL для удаления заметки
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

    def setUp(self):
        """Очищает БД в начале каждого теста."""
        self.note.delete()
        self.note = Note.objects.create(
            title='Заголовок',
            text=self.NOTE_TEXT,
            slug='Slug',
            author=self.author
        )

    def test_author_can_edit_note(self):
        """
        Тест edit/.

        Проверка на доступ автора к изменению своей заметки.
        """
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, URL_TO_DONE)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.UPDATE_NOTE_TEXT)
        self.assertEqual(self.note.title, self.UPDATE_NOTE_TITLE)
        self.assertEqual(self.note.slug, self.UPDATE_NOTE_SLUG)
        self.assertEqual(self.note.author, self.author)

    def test_author_can_delete_note(self):
        """
        Тест delete/.

        Проверка на доступ автора к удалению своей заметки.
        """
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, URL_TO_DONE)
        self.assertFalse(Note.objects.filter(id=self.note.id).exists())

    def test_user_cant_edit_note_of_another_user(self):
        """
        Тест edit/.

        Проверка на доступ пользователя к редактированию
        не своей заметки.
        """
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note = Note.objects.get(id=self.note.id)
        self.assertEqual(note.text, self.note.text)
        self.assertEqual(note.title, self.note.title)
        self.assertEqual(note.slug, self.note.slug)
        self.assertEqual(note.author, self.author)

    def test_user_cant_delete_note_of_another_user(self):
        """
        Тест delete/.

        Проверка на доступ пользователя к удалению
        не своей заметки.
        """
        response = self.client.post(self.delete_url)
        self.assertRedirects(
            response, f'{URL_TO_LOGIN}?next={self.delete_url}'
        )
        self.assertTrue(Note.objects.filter(id=self.note.id).exists())

    def test_not_unique_slug(self):
        """Тест на неуникальный slug."""
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(URL_TO_ADD, data=self.form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)
