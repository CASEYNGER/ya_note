import pytest

from django.test.client import Client

from notes.models import Note


@pytest.fixture
# Встроенная фикструа для модели пользователей
def author(django_user_model):
    """Создаем пользователя-автора."""
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def not_author(django_user_model):
    """Создаем пользователя-не автора."""
    return django_user_model.objects.create(username='Не автор')


@pytest.fixture
# Вызываем фикстуру автора
def author_client(author):
    # Создаем новый экземпляр клиента, чтобы не менять глобальный
    client = Client()
    # Логиним автора в клиенте
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author):
    # Создаем новый экземпляр клиента, чтобы не менять глобальный
    client = Client()
    # Логиним обычного пользователя в клиенте
    client.force_login(not_author)
    return client


@pytest.fixture
def note(author):
    # Создаем объект заметки
    note = Note.objects.create(
        title='Заголовок',
        text='Текст заметки',
        slug='note-slug',
        author=author
    )
    return note


@pytest.fixture
def slug_for_args(note):
    # Возвращает кортеж, который содержит slug заметки.
    # На то, что это кортеж, указывает запятая в конце выражения
    return (note.slug,)
