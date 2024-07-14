import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from store.models import Book
from store.serializers import BookSerializer


class BooksApiTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_username')

        self.book_1 = Book.objects.create(name='Test book 1', author_name='Author 1', price=25, owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', author_name='Author 5', price=75, owner=self.user)
        self.book_3 = Book.objects.create(name='Test book Author 1', author_name='Author 2', price=55, owner=self.user)

    def test_get_detail(self):
        url = reverse('book-detail', args=(self.book_2.id,))
        response = self.client.get(url)
        serializer_data = BookSerializer(self.book_2).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_list(self):
        # возвращает маршрут с именем book-list
        url = reverse('book-list')
        print(url)
        # клиентский get запрос по апи адресу
        response = self.client.get(url)
        # print(response.data)
        serializer_data = BookSerializer([self.book_1, self.book_2, self.book_3], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_filter(self):
        # возвращает маршрут с именем book-list
        url = reverse('book-list')
        # print(url)
        # клиентский get запрос по апи адресу
        response = self.client.get(url, data={'price': 55})
        # print(response.data)
        serializer_data = BookSerializer([self.book_3], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_search(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'search': 'Author 1'})
        serializer_data = BookSerializer([self.book_1, self.book_3], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_ordering(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'ordering': '-price'})
        serializer_data = BookSerializer([self.book_2, self.book_3, self.book_1], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_create(self):
        # проверяем количество книг перед созданием книги
        self.assertEqual(3, Book.objects.all().count())
        url = reverse('book-list')
        data = {
            'name': 'Programing in Python 3',
            'price': 150,
            'author_name': 'Mark Summerfield'
        }
        # преобразуем словарь в json строку
        json_data = json.dumps(data)

        # авторизуемся с помощю созданнго юзера
        self.client.force_login(self.user)

        response = self.client.post(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(4, Book.objects.all().count())
        self.assertEqual(self.user, Book.objects.last().owner)

    def test_update(self):
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            'name': self.book_1.name,
            'price': 575,
            'author_name': self.book_1.author_name
        }
        # преобразуем словарь в json строку
        json_data = json.dumps(data)

        # авторизуемся с помощю созданнго юзера
        self.client.force_login(self.user)

        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        # обновляем запись из дб
        self.book_1.refresh_from_db()
        self.assertEqual(575, self.book_1.price)

    def test_update_not_owner(self):
        self.user2 = User.objects.create(username='test_username2')
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            'name': self.book_1.name,
            'price': 575,
            'author_name': self.book_1.author_name
        }
        # преобразуем словарь в json строку
        json_data = json.dumps(data)

        # авторизуемся с помощю созданнго юзера
        self.client.force_login(self.user2)

        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': ErrorDetail(string='You do not have permission to perform this action.', code='permission_denied')}, response.data)
        # обновляем запись из дб
        self.book_1.refresh_from_db()
        self.assertEqual(25, self.book_1.price)

    def test_update_not_owner_but_staff(self):
        self.user2 = User.objects.create(username='test_username2', is_staff=True)
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            'name': self.book_1.name,
            'price': 575,
            'author_name': self.book_1.author_name
        }
        # преобразуем словарь в json строку
        json_data = json.dumps(data)

        # авторизуемся с помощю созданнго юзера
        self.client.force_login(self.user2)

        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # обновляем запись из дб
        self.book_1.refresh_from_db()
        self.assertEqual(575, self.book_1.price)

    def test_delete(self):
        url = reverse('book-detail', args=(self.book_3.id,))

        # для всех манипуляций с обьектами нужно быть авторизованным
        self.client.force_login(self.user)

        response = self.client.delete(url)
        exist = Book.objects.filter(id=self.book_3.id).exists()
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(False, exist)

    def test_delete_not_owner(self):
        self.user2 = User.objects.create(username='Test_user2')
        url = reverse('book-detail', args=(self.book_3.id,))

        # для всех манипуляций с обьектами нужно быть авторизованным
        self.client.force_login(self.user2)

        response = self.client.delete(url)
        exist = Book.objects.filter(id=self.book_3.id).exists()
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(True, exist)
