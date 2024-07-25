from django.contrib.auth.models import User
from django.db import models
from django.db.models import UniqueConstraint


class Book(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    price = models.DecimalField(max_digits=7, decimal_places=2, verbose_name='Цена')
    author_name = models.CharField(max_length=255, verbose_name='Имя автора')
    discount = models.SmallIntegerField(default=0, null=True, verbose_name='Скидка')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='my_books', verbose_name='Владелец')
    # явно связываем отношение ManyToMany через нашу таблицу, чтобы добавить в неё дополнительные поля
    # так как у нас дво поля связанны с User, возникает конфликт при обращении от юзера к книгам,
    # user.book (то ли прочитал, то ли написал), для этого прописываем related_name, по умолчанию related_name=book_set()
    # на к двум полям нельзя применить одинаковое название, для одной из связей нужно изменить название на своё
    readers = models.ManyToManyField(User, through='UserBookRelation', related_name='books')

    # кеширующее поле, если происходит конфликт при создании миграции удаляем одноимённое поле из вью
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=None, null=True)

    def __str__(self):
        return f"Id {self.id}: {self.name}"


class UserBookRelation(models.Model):
    RATE_CHOICES = (
        (1, 'Ok'),
        (2, 'Fine'),
        (3, 'Good'),
        (4, 'Amazing'),
        (5, 'Incredible')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    like = models.BooleanField(default=False)
    in_bookmarks = models.BooleanField(default=False)
    rate = models.PositiveSmallIntegerField(choices=RATE_CHOICES, null=True)

    def __str__(self):
        return f'{self.user.username}: {self.book.name}, RATE {self.rate}'

    # В Python метод __init__ является конструктором класса. Этот метод вызывается автоматически при создании нового
    # объекта класса и используется для инициализации его атрибутов. Конструктор __init__ позволяет задавать начальные
    # значения переменных объекта и выполнять другие действия при создании экземпляра класса.
    # переопределяем метод __init__ модели
    def __init__(self, *args, **kwargs):
        # вызываем родительский метод super.__init__ чтобы он не перезаписался
        super(UserBookRelation, self).__init__(*args, **kwargs)
        # берём заначение поля rate до сохранения записи
        self.old_rating = self.rate

    def save(self, *args, **kwargs):
        # делаем локальный импорт чтобы избежать перекрёстного импорта, (в фунцию set_rating() мы импортировали данный класс)
        from store.logic import set_rating

        # если происходит создание записи то пк ещё не существует
        creating = not self.pk

        super().save(*args, **kwargs)

        new_rating = self.rate
        # print('new_rating', new_rating)

        # если новый рейтинг не равен старому рейтингу, либо это создание записи
        if self.old_rating != new_rating or creating:

            # вызываем функцию обновления рейтинга
            set_rating(self.book)

        # set_rating(self.book)

    # ограничения для связи ManyToMany: не может существовоть двух записей с одинаковыми значениями полей
    constraints = [UniqueConstraint(fields=['user', 'book'], name='unique-like')]