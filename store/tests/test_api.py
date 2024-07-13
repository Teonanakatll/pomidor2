from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from store.models import Book
from store.serializers import BookSerializer


class BooksApiTestCase(APITestCase):
    def setUp(self):
        self.book_1 = Book.objects.create(name='Test book 1', author_name='Author 1', price=25)
        self.book_2 = Book.objects.create(name='Test book 2', author_name='Author 5', price=75)
        self.book_3 = Book.objects.create(name='Test book Author 1', author_name='Author 2', price=55)

    def test_get(self):
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
        serializer_data = BookSerializer([self.book_2, self.book_3], many=True).data
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