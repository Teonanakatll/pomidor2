from django.db.models import Avg

from store.models import UserBookRelation


# aggregate() - возвращает словарь из тех полей которые мы передали и тех значений которые мы им присвоили
# берём значение по ключу
def set_rating(book):
    rating = UserBookRelation.objects.filter(book=book).aggregate(rating=Avg('rate')).get('rating')
    # присваиваем значение переданной книге
    book.rating = rating
    book.save()