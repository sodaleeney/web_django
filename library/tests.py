from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Book

class LibraryAppTests(TestCase):

    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass')
        # Создаем книги
        self.book1 = Book.objects.create(title='Book One', author='Author A')
        self.book2 = Book.objects.create(title='Book Two', author='Author B')
        self.client = Client()

    def test_register(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123'
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_and_cookies(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('book_list'))
        # Проверяем установку cookie user_id и username
        self.assertIn('user_id', response.cookies)
        self.assertIn('username', response.cookies)
        session = self.client.session
        self.assertEqual(session['user_id'], self.user.id)
        self.assertEqual(session['username'], self.user.username)

    def test_book_list_access(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Book One')
        self.assertContains(response, 'Book Two')

    def test_add_book_duplicate(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('add_book'), {
            'title': 'Book One',
            'author': 'Author A'
        }, follow=True)
        form = response.context['form']
        self.assertFormError(form, None, 'Книга с таким названием и автором уже существует.')

    def test_add_book_success(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('add_book'), {
            'title': 'New Book',
            'author': 'New Author'
        })
        self.assertRedirects(response, reverse('book_list'))
        self.assertTrue(Book.objects.filter(title='New Book', author='New Author').exists())

    def test_delete_book_permission(self):
        # Попытка удалить книг обычным пользователем
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('delete_book', args=[self.book1.pk]))
        self.assertEqual(response.status_code, 403)

        # Удаление суперпользователем
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('delete_book', args=[self.book1.pk]))
        self.assertRedirects(response, reverse('book_list'))
        self.assertFalse(Book.objects.filter(pk=self.book1.pk).exists())

    def test_mark_books_read(self):
        self.client.login(username='testuser', password='password123')
        # Отметить book1 и book2 как прочитанные
        response = self.client.post(reverse('book_list'), {'book_id': [str(self.book1.pk), str(self.book2.pk)]})
        self.assertRedirects(response, reverse('book_list'))
        self.assertIn(self.book1, self.user.read_books.all())
        self.assertIn(self.book2, self.user.read_books.all())

        # Снять отметку с book1
        response = self.client.post(reverse('book_list'), {'book_id': [str(self.book2.pk)]})
        self.assertRedirects(response, reverse('book_list'))
        self.assertNotIn(self.book1, self.user.read_books.all())
        self.assertIn(self.book2, self.user.read_books.all())

