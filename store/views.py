from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet

from store.models import Book
from store.permissions import IsOwnerOrStaffOrReadOnly
from store.serializers import BookSerializer


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

def auth(request):
    return render(request, 'oauth.html')
