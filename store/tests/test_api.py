import json

from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Count, Case, When, Avg, F, Prefetch
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase
from django.test.utils import CaptureQueriesContext

from store.models import Book, UserBookRelation
from store.serializers import BookSerializer


class BooksApiTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_username')

        self.book_1 = Book.objects.create(name='Test book 1', author_name='Author 1', price=25,
                                          discount=10, owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', author_name='Author 5', price=75,
                                          discount=20, owner=self.user)
        self.book_3 = Book.objects.create(name='Test book Author 1', author_name='Author 2', price=55,
                                          discount=30, owner=self.user)

        UserBookRelation.objects.create(user=self.user, book=self.book_1, like=True, rate=5)

    def test_get_detail(self):
        url = reverse('book-detail', args=(self.book_1.id,))
        response = self.client.get(url)

        # сериализатор отправляет данные с аннотированным полем, поэтому добавим его
        book = Book.objects.filter(id=self.book_1.id).annotate(annotated_likes=
                                       Count(Case(When(userbookrelation__like=True, then=1))),
                                       # rating=Avg('userbookrelation__rate'),
                                       price_with_discount=F('price') - (F('price') / 100) * F('discount'),
                                       owner_name=F('owner__username')).prefetch_related(
                                       Prefetch('readers', User.objects.all().only('first_name', 'last_name')))

        book = book[0]

        serializer_data = BookSerializer(book, many=False).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(serializer_data['rating'], '5.00')
        self.assertEqual(serializer_data['price_with_discount'], '22.50')

    def test_get_list(self):
        # возвращает маршрут с именем book-list
        url = reverse('book-list')

        # тестируем select_related() u prefetch_related в connection отлавливаем query-запросы
        with CaptureQueriesContext(connection) as queries:
            # client - клиентский запрос по апи адресу
            response = self.client.get(url)
        self.assertEqual(2, len(queries))

        # клиентский get запрос по апи адресу
        response = self.client.get(url)

        books = Book.objects.all().annotate(annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
                                    # rating=Avg('userbookrelation__rate'),
                                    price_with_discount=F('price') - (F('price') / 100) * F('discount'),
                                    owner_name=F('owner__username')).prefetch_related(
                                    Prefetch('readers', queryset=User.objects.all().only('first_name', 'last_name'))).order_by('id')

        serializer_data = BookSerializer(books, many=True).data
        # print(serializer_data)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(serializer_data[0]['rating'], '5.00')
        # self.assertEqual(serializer_data[0]['likes_count'], 1)
        self.assertEqual(serializer_data[0]['annotated_likes'], 1)

    def test_get_filter(self):
        # возвращает маршрут с именем book-list
        url = reverse('book-list')
        # print(url)
        # клиентский get запрос по апи адресу
        response = self.client.get(url, data={'price': 55})

        books = Book.objects.filter(id=self.book_3.id).annotate(annotated_likes=
                                Count(Case(When(userbookrelation__like=True, then=1))),
                                # rating=Avg('userbookrelation__rate'),
                                price_with_discount=F('price') - (F('price') / 100) * F('discount'),
                                owner_name=F('owner__username')).prefetch_related(
                                Prefetch('readers', User.objects.all().only('first_name', 'last_name'))).order_by('id')

        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_search(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'search': 'Author 1'})

        books = Book.objects.filter(id__in=[self.book_1.id, self.book_3.id]).annotate(annotated_likes=
                            Count(Case(When(userbookrelation__like=True, then=1))),
                            # rating=Avg('userbookrelation__rate'),
                            price_with_discount=F('price') - (F('price') / 100) * F('discount'),
                            owner_name=F('owner__username')).prefetch_related(
                            Prefetch('readers', User.objects.all().only('first_name', 'last_name'))).order_by('id')

        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_ordering(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'ordering': '-price'})

        books = Book.objects.filter(id__in=[self.book_2.id, self.book_3.id, self.book_1.id]).annotate(annotated_likes=
                            Count(Case(When(userbookrelation__like=True, then=1))),
                            # rating=Avg('userbookrelation__rate'),
                            price_with_discount=F('price') - (F('price') / 100) * F('discount'),
                            owner_name=F('owner__username')).prefetch_related(
                            Prefetch('readers', User.objects.all().only('first_name', 'last_name'))).order_by('-price')

        serializer_data = BookSerializer(books, many=True).data
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


class BookRelationTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_username')
        self.user2 = User.objects.create(username='test_username2')

        self.book_1 = Book.objects.create(name='Test book 1', author_name='Author 1', price=25, owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', author_name='Author 5', price=75, owner=self.user)

    def test_like(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))

        data = {
            'like': True
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)

        self.assertTrue(relation.like)

        # тест добавления в закладки
        data = {
            'in_bookmarks': True
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)
        self.assertTrue(relation.in_bookmarks)

    def test_rate(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))

        data = {
            'rate': 3
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)

        # self.assertEqual(3, response.data['rate'])
        self.assertEqual(3, relation.rate)

    def test_rate_wrong(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))

        data = {
            'rate': 6
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')

        # третьим аргументом можно передать значение которое выведется принтом если первые два аргумента не равны response.data
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)

        # self.assertEqual(3, response.data['rate'])
        self.assertEqual(None, relation.rate)
