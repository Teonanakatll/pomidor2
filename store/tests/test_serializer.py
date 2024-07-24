# from django.test import TestCase
from django.db.models import Count, Case, When, Avg, F, Prefetch
from django.test import TestCase

from django.contrib.auth.models import User

from store.models import Book, UserBookRelation
from store.serializers import BookSerializer


class BookSerializerTestCase(TestCase):
    def test_ok(self):
        user1 = User.objects.create(username='user1', first_name='Fedor', last_name='Fundukov')
        user2 = User.objects.create(username='user2', first_name='Igor', last_name='Rubakov')
        user3 = User.objects.create(username='user3', first_name='Monya', last_name='Cherpakov')

        book_1 = Book.objects.create(name='Test book 1', price=25, discount=10, author_name='Author 1', owner=user1)
        book_2 = Book.objects.create(name='Test book 2', price=55, discount=20, author_name='Author 2')

        UserBookRelation.objects.create(user=user1, book=book_1, like=True, rate=5)
        UserBookRelation.objects.create(user=user2, book=book_1, like=True, rate=5)
        UserBookRelation.objects.create(user=user3, book=book_1, like=True, rate=4)

        UserBookRelation.objects.create(user=user1, book=book_2, like=True, rate=3)
        UserBookRelation.objects.create(user=user2, book=book_2, like=True, rate=4)
        # для корректного тестирования вожно проверять и False зночения, чтобы отслеживать все изменения в
        # логике тестируемого функционала
        UserBookRelation.objects.create(user=user3, book=book_2, like=False)

        # Case() используется для создания условных выражений в запросах к бд. Он позволяет выполнять sql-подобные
        # условия (как CASE в sql), когда нужно выполнить различные действия в зависимости от значения полей.
        # When() - указывает когда необходимо подсчитывать значения. then - в током случае возвращаем 1
        #
        # бывает сбивается сортировка, в таком случае добавляем order_by('id')
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rate'),
            price_with_discount=F('price') - (F('price') / 100) * F('discount'),
            owner_name=F('owner__username')

            ).prefetch_related(
                Prefetch('readers', queryset=User.objects.all().only('first_name', 'last_name'))).order_by('id')

        data = BookSerializer(books, many=True).data
        print(data)
        expected_data = [
            {
                'id': book_1.id,
                'name': 'Test book 1',
                'price': '25.00',
                'discount': 10,
                'price_with_discount': '22.50',
                'author_name': 'Author 1',
                'owner_name': 'user1',
                # 'likes_count': 3,
                'annotated_likes': 3,
                'rating': '4.67',
                'readers': [
                    {'first_name': 'Fedor', 'last_name': 'Fundukov'},
                    {'first_name': 'Igor', 'last_name': 'Rubakov'},
                    {'first_name': 'Monya', 'last_name': 'Cherpakov'},
                ]
            },
            {
                'id': book_2.id,
                'name': 'Test book 2',
                'price': '55.00',
                'discount': 20,
                'price_with_discount': '44.00',
                'author_name': 'Author 2',
                'owner_name': None,
                # 'likes_count': 2,
                'annotated_likes': 2,
                'rating': '3.50',
                'readers': [
                    {'first_name': 'Fedor', 'last_name': 'Fundukov'},
                    {'first_name': 'Igor', 'last_name': 'Rubakov'},
                    {'first_name': 'Monya', 'last_name': 'Cherpakov'},
                ]
            },
        ]
        # print(data)

        self.assertEqual(expected_data, data)
