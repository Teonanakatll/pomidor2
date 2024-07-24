from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from store.models import Book, UserBookRelation


# Роль сериализатора: конвертирование произвольных обьектов языка python в формат json, в том числе обьекты моделей
# и кверисеты, и наоборои из json в соответствующие обьекты языка python

# сериализатор для отображения вложеных полей модели User (поле readers ManyToMany)
class BookReaderSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')


class BookSerializer(ModelSerializer):
    # поле для сериализации вычисленных данных созданного нами метора get_likes_count
    # при обьявлении метода синтаксис get_имя созданного поля сериализатора
    # likes_count = serializers.SerializerMethodField()

    # поля сериализатора созданные с помощю аннотирования необходимо установить read_only=True
    annotated_likes = serializers.IntegerField(read_only=True)
    rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    price_with_discount = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)

    # через Foreignkey на модель owner берём значение значение поля username,
    # если у книги нет овнера default=''
    # чтобы не было N+1 во вью выбираем owner через select_related, source - источник данных для поля сериализатора
    # owner_name = serializers.CharField(source='owner.username', default='', read_only=True)

    owner_name = serializers.CharField(read_only=True)

    # добавляем поле которому присваиваем результат работы дпугого сериалайзера для добавления вложенных полей из связaнных записей
    # через связь ManyToMany (поле readers), поле должно называться как и поле в модели Book те readers
    # если хотим указать другое имя, то необходимо указать source='readers' в параметрах
    readers = BookReaderSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = ('id', 'name', 'price', 'discount', 'price_with_discount',
                  'author_name', 'owner_name', 'annotated_likes', 'rating', 'readers')  # , 'likes_count'

    # пишем свою функцию для созданного поля сер. (likes_count), эта также можно сделать с помощю анотации
    # self- сам сериализатор, instance - это книга которую мы в данный момент сериализуем
    # добовляет n+1 (дополнительный запрос к каждой записи
    # def get_likes_count(self, instance):
    #     # фильтруем записи UserBookRelation по текущей книге с like=True и считаем их кол-во
    #     return UserBookRelation.objects.filter(book=instance, like=True).count()


class UserBookRelationSerializer(ModelSerializer):
    class Meta:
        model = UserBookRelation
        fields = ('book', 'like', 'in_bookmarks', 'rate')
