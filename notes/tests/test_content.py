from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestContent(TestCase):
    """
    Класс тестов, унаследованный от TestCase.

    Проверяет попадание в список заметок одного пользователя
    заметок другого, передачу форм на страницы создания и редактирования
    заметки, а также передачу отдельной заметки на страницу со списком заметок
    в списке object_list в словаре context.
    """

    LIST_URL = reverse('notes:list')
    ADD_URL = reverse('notes:add')

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

        # URL для edit
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))

    def test_notes_list_for_auth_user(self):
        """
        Тест для отдельной заметки.

        Аутентифицированный пользователь видит свои заметки в списках.
        """
        response = self.author_client.get(self.LIST_URL)
        notes = response.context['object_list']
        self.assertIn(self.note, notes)

    def test_notes_list_for_anonymous_user(self):
        """Анонимный пользователь не видит чужие заметки."""
        response = self.reader_client.get(self.LIST_URL)
        notes = response.context['object_list']
        self.assertNotIn(self.note, notes)

    def test_add_and_edit_note_pages_send_forms(self):
        """Страницы добавления и редактирования заметки содержат формы."""
        urls = (
            self.ADD_URL,
            self.edit_url
        )
        for url in urls:
            response = self.author_client.get(url)
            self.assertIn('form', response.context)
            self.assertIsInstance(response.context['form'], NoteForm)
