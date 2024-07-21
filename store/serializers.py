from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from store.models import Book, UserBookRelation


class BookSerializer(ModelSerializer):
    # поле для сериализации вычисленных данных созданного нами метора get_likes_count
    # при обьявлении метода синтаксис get_имя созданного поля сериализатора
    likes_count = serializers.SerializerMethodField()

    # поля сериализатора созданные с помощю аннотирования необходимо установить read_only=True
    annotated_likes = serializers.IntegerField(read_only=True)
    rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    price_with_discount = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)

    class Meta:
        model = Book
        fields = ('id', 'name', 'price', 'discount', 'price_with_discount', 'author_name', 'owner', 'likes_count', 'annotated_likes', 'rating')

    # пишем свою функцию для созданного поля сер. (likes_count), эта также можно сделать с помощю анотации
    # self- сам сериализатор, instance - это книга которую мы в данный момент сериализуем
    # добовляет n+1 (дополнительный запрос к каждой записи
    def get_likes_count(self, instance):
        # фильтруем записи UserBookRelation по текущей книге с like=True и считаем их кол-во
        return UserBookRelation.objects.filter(book=instance, like=True).count()


class UserBookRelationSerializer(ModelSerializer):
    class Meta:
        model = UserBookRelation
        fields = ('book', 'like', 'in_bookmarks', 'rate')
