from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from store.models import Book, UserBookRelation
from store.permissions import IsOwnerOrStaffOrReadOnly
from store.serializers import BookSerializer, UserBookRelationSerializer


class BookViewSet(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # указываем поля для фильтрации, поиска и сортировки
    filterset_fields = ['price']                  # ?price=
    search_fields = ['name', 'author_name']       # ?search=
    ordering_fields = ['price', 'author_name']    # ?ordering=   price   -price

    permission_classes = [IsOwnerOrStaffOrReadOnly]

    # чтобы добавить request юзера в качестве хозяина книги при добавлении записи чезез api
    # переопределим метод perform_create (чтобы не менять стандартное поведения метода create)
    def perform_create(self, serializer):
        # берём данные сериализатора и добавляем в него словарь 'owner': request.user
        serializer.validated_data['owner'] = self.request.user
        serializer.save()


class UserBookRelationView(UpdateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = UserBookRelation.objects.all()
    serializer_class = UserBookRelationSerializer

    # lookup_field - Поле цели, которое должно быть использовано для поиска. Должно соответствовать
    # аргументу ключевого слова URL в ссылающемся представлении.
    lookup_field = 'book'

    # в lookup_field мы передаём id книги, но этого недастаточно, нужно ещё передать id юзера чтобы найти
    # эту связь, в UserBookRelation два поля ForeignKey, переопределим метод get_object
    def get_object(self):
        # если юзер первый раз ставит лайк то мы не сможем получить его UserBookRelation, в таком случае создаём эту свзь
        # передаём юзера и именованный параметр 'book' пришедший через lookup_field
        obj, created = UserBookRelation.objects.get_or_create(user=self.request.user, book_id=self.kwargs['book'])
        # print('created', created)
        return obj

def auth(request):
    return render(request, 'oauth.html')
