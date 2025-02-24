import pytest

from http import HTTPStatus

from django.urls import reverse

from pytest_django.asserts import assertRedirects


@pytest.mark.parametrize(
    'name',  # Имя параметра функции
    # Значения, которые будут передаваться в name
    ('notes:home', 'users:login', 'users:logout', 'users:signup'),
)
# Указываем в фикстурах встроенный клиент
def test_home_availability_for_anonymous_user(client, name):
    """Проверка, что анонимному пользователью доступна главная страница."""
    url = reverse(name)  # Получаем ссылку на нужный адрес
    response = client.get(url)  # Выполняем запрос
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',
    ('notes:list', 'notes:add', 'notes:success'),
)
def test_pages_availability_for_auth_user(not_author_client, name):
    """Проверка, что страница доступна авторизованному пользователю."""
    url = reverse(name)
    response = not_author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete'),
)
def test_pages_availability_for_author(author_client, name, note):
    """Проверка, что страница доступна автору."""
    url = reverse(name, args=(note.slug,))
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    # Предварительно оборачиваем имена фикстур
    # в вызов функции pytest.lazy_fixture().
    (
        (pytest.lazy_fixture('not_author_client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
)
@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete'),
)
# В параметры теста добавляем имена parametrized_client и expected_status
def test_pages_availability_for_different_users(
    parametrized_client, name, note, expected_status
):
    """Проверка, что страница доступна разным пользователям."""
    url = reverse(name, args=(note.slug,))
    # Делаем запрос от имени клиента parametrized_client
    response = parametrized_client.get(url)
    # Ожидаем ответ страницы, указанный в expected_status
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:detail', pytest.lazy_fixture('slug_for_args')),
        ('notes:edit', pytest.lazy_fixture('slug_for_args')),
        ('notes:delete', pytest.lazy_fixture('slug_for_args')),
        ('notes:add', None),
        ('notes:success', None),
        ('notes:list', None),
    ),
)
# Передаем в тест анонимный клиент, name проверяемых страниц и note_object
def test_redirects(client, name, args):
    """Проверка редиректов."""
    login_url = reverse('users:login')
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    # Ожидаем, что со всех проверяемых страниц анонимный клиент
    # будет перенаправлен на страницу логина
    assertRedirects(response, expected_url)