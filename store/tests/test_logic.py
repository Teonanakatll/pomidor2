from unittest import expectedFailure

from django.test import TestCase

from django.contrib.auth.models import User

from store.logic import set_rating
from store.models import UserBookRelation, Book


class SetRatingTestCase(TestCase):
    def setUp(self):

        user1 = User.objects.create(username='user1', first_name='Fedor', last_name='Fundukov')
        user2 = User.objects.create(username='user2', first_name='Igor', last_name='Rubakov')
        user3 = User.objects.create(username='user3', first_name='Monya', last_name='Cherpakov')

        self.book_1 = Book.objects.create(name='Test book 1', price=25, discount=10, author_name='Author 1', owner=user1)

        UserBookRelation.objects.create(user=user1, book=self.book_1, like=True, rate=5)
        UserBookRelation.objects.create(user=user2, book=self.book_1, like=True, rate=5)
        UserBookRelation.objects.create(user=user3, book=self.book_1, like=True, rate=4)



    def test_ok(self):
        set_rating(self.book_1)
        self.book_1.refresh_from_db()
        self.assertEqual('4.67', str(self.book_1.rating))

    # тест для связи ManyToMany: не может существовоть двух записей с одинаковыми значениями полей
    @expectedFailure
    def test_double_relation(self):
        self.relation1 = UserBookRelation.objects.create(user=self.user1, book=self.book_1, rate=5, like=True)
