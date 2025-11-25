from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponseForbidden
from .models import Book
from .forms import BookForm


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # регистрация не логиним пользователя автоматически, переходим на логин
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'library/registration.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Сохраняем данные пользователя в сессии
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            # Создаем редирект и устанавливаем cookie
            response = redirect('book_list')
            response.set_cookie('user_id', str(user.id), max_age=3600*24*365)
            response.set_cookie('username', user.username, max_age=3600*24*365)
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, request.LANGUAGE_CODE, max_age=3600*24*365)
            return response
    else:
        form = AuthenticationForm()
    return render(request, 'library/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def book_list(request):
    books = Book.objects.all()
    user_books = request.user.read_books.all()

    if request.method == 'POST':
        selected_books_ids = request.POST.getlist('book_id')
        selected_books_ids_set = set(map(int, selected_books_ids))
        current_books_ids_set = set(book.id for book in user_books)

        for book_id in selected_books_ids_set - current_books_ids_set:
            book = Book.objects.get(id=book_id)
            request.user.read_books.add(book)

        for book_id in current_books_ids_set - selected_books_ids_set:
            book = Book.objects.get(id=book_id)
            request.user.read_books.remove(book)

        return redirect('book_list')

    context = {
        'books': books,
        'user_books': user_books,
        'user_id': request.session.get('user_id'),
        'username': request.session.get('username'),
        'language': request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, settings.LANGUAGE_CODE),
    }
    return render(request, 'library/book_list.html', context)


@login_required
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            author = form.cleaned_data['author']

            if Book.objects.filter(title=title, author=author).exists():
                form.add_error(None, 'Книга с таким названием и автором уже существует.')
                return render(request, 'library/add_book.html', {'form': form})
            else:
                book = form.save()
                book.readers.add(request.user)
                return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'library/add_book.html', {'form': form})



@login_required
def delete_book(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав на удаление книги.")
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    messages.success(request, 'Книга успешно удалена.')
    return redirect('book_list')
