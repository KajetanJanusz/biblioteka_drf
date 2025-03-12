from datetime import date, timedelta
from typing import Any
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView, CreateAPIView
from django.db.models import Exists, OuterRef

from django.contrib import messages
from django.db.models.query import QuerySet
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Case, When, Value, IntegerField, Sum
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from core import schemas
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from books.models import (
    Badge,
    Book,
    BookRental,
    BookCopy,
    Category,
    Notification,
    Opinion,
)
from books import serializers
from core.permissions import (
    IsCustomerPermission,
    IsAdminPermission,
    IsEmployeePermission,
)
from books.models import CustomUser
from core.helpers import get_five_book_articles
from core.ai import get_ai_book_recommendations, get_ai_generated_description


class DashboardClientView(APIView):
    """
    Widok pulpitu klienta wyświetlający spersonalizowane informacje użytkownika.

        Funkcje:
        - Wyświetla wypożyczone książki
        - Pokazuje nieprzeczytane powiadomienia
        - Prezentuje opinie użytkownika o książkach
        - Udostępnia rekomendacje książek

        Wymaga logowania i dostępu klienta.
    """

    permission_classes = [IsAuthenticated, IsCustomerPermission]

    # @schemas.dashboard_client_schema
    def get(self, request, pk=None):
        user = request.user

        if "ai_recommendations" in request.session:
            ai_recommendations = request.session["ai_recommendations"]
        else:
            ai_recommendations = get_ai_book_recommendations(
                list(BookRental.objects.filter(user=user))
            )
            request.session["ai_recommendations"] = ai_recommendations

        rented_books = BookRental.objects.filter(
            Q(user=user.id)
            & (Q(status="rented") | Q(status="pending") | Q(status="overdue"))
        )
        rented_books_old = BookRental.objects.filter(user=user, status="returned")
        notifications = Notification.objects.filter(
            user=user, is_read=False, is_available=True
        )
        opinions = Opinion.objects.filter(user=user)
        badges = Badge.objects.get(user=user)

        total_other_users = CustomUser.objects.all().count()
        average_user_rents = 0
        if total_other_users > 0:
            average_user_rents = (
                BookRental.objects.exclude(user=user).count() / total_other_users
            )

        all_my_rents = BookRental.objects.filter(user=user).count()

        books_in_categories = (
            BookRental.objects.filter(user=user)
            .values("book_copy__book__category__name")
            .annotate(count=Count("book_copy__book__category"))
            .order_by("book_copy__book__category__name")
        )

        response_data = {
            "username": user.username,
            "rented_books": serializers.BookRentalSerializer(
                rented_books, many=True
            ).data,
            "rented_books_old": serializers.BookRentalSerializer(
                rented_books_old, many=True
            ).data,
            "notifications": serializers.NotificationSerializer(
                notifications, many=True
            ).data,
            "opinions": serializers.OpinionSerializer(opinions, many=True).data,
            "ai_recommendations": ai_recommendations,
            "badges": serializers.BadgeSerializer(badges).data,
            "average_user_rents": average_user_rents,
            "all_my_rents": all_my_rents,
            "books_in_categories": list(books_in_categories),
        }

        return Response(response_data, status=status.HTTP_200_OK)


class ArticlesView(APIView):
    """
    API zwracające artykuły o książkach.
    Wymaga uwierzytelnienia.
    """
    permission_classes = [IsAuthenticated, IsCustomerPermission]

    # @schemas.articles_view_customer_schema
    def get(self, request, *args, **kwargs):
        if "articles" in request.session:
            articles = request.session["articles"]
        else:
            request.session["articles"] = articles = get_five_book_articles()

        return Response({"articles": articles})


class MarkNotificationAsReadView(APIView):
    """
    API do oznaczania powiadomień jako przeczytane.
    Wymaga uwierzytelnienia i uprawnień klienta.
    """
    permission_classes = [IsAuthenticated, IsCustomerPermission]

    # @schemas.mark_notification_as_read_customer_schema
    def post(self, request, pk):
        serializer = serializers.MarkReadNotificationAsReadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.error_messages}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            notification = Notification.objects.get(id=request.data["id"])
        except Notification.DoesNotExist:
            return Response(
            {"error": "Niepoprawne id.",},
            status=status.HTTP_400_BAD_REQUEST
        )

        notification.is_read = True
        notification.save()
        
        return Response(
            {"message": "Odczytane.",},
            status=status.HTTP_200_OK
        )


class BorrowBookView(APIView):
    """
    Widok obsługujący proces wypożyczania książek.

        Funkcje:
        - Sprawdza dostępność książki
        - Ogranicza użytkownika do 3 jednoczesnych wypożyczeń
        - Tworzy nowe wypożyczenie
        - Aktualizuje status egzemplarza książki

        Wymaga logowania i dostępu klienta.
    """

    permission_classes = [IsAuthenticated, IsCustomerPermission]

    # @schemas.borrow_book_customer_schema
    def post(self, request, pk):
        serializer = serializers.BorrowBookSerializer(data=request.data)
        user = request.user
        
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        book = Book.objects.get(id=serializer.validated_data["id"])

        available_copy = (
            BookCopy.objects.select_related("book")
            .filter(book=book, is_available=True)
            .first()
        )
        
        if not available_copy:
            return Response(
                {"error": "Nie ma wolnych egzemplarzy"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_rentals_count = BookRental.objects.filter(
            Q(user=user.id) & (Q(status="rented") | Q(status="pending"))
        ).count()

        if user_rentals_count >= 3:
            return Response(
                {"error": f"Zwróć inną książkę, żeby wypożyczyć {book.title}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        available_copy.is_available = False
        available_copy.borrower = user
        available_copy.save()

        rental = BookRental.objects.create(
            book_copy=available_copy,
            user=user,
            rental_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status="rented",
        )
        
        rental_data = {
            "book_title": book.title,
            "rental_date": rental.rental_date,
            "due_date": rental.due_date,
            "status": rental.status,
            "status_display": rental.get_status_display(),
        }

        return Response(
            {
                "message": "Książka wypożyczona",
                "rental": rental_data
            },
            status=status.HTTP_201_CREATED
        )


class ReturnBookView(APIView):
    """
    API obsługujące zwrot książki.

    Funkcje:
    - Zmienia status wypożyczenia na 'pending' (oczekujący na zatwierdzenie)
    - Zwraca potwierdzenie zwrotu
    - Aktualizuje powiadomienia

    Wymaga logowania i dostępu klienta.
    """
    permission_classes = [IsAuthenticated, IsCustomerPermission]

    # @schemas.return_book_customer_schema
    def post(self, request, pk):
        """Obsługuje zwrot książki"""
        serializer = serializers.RentalIDSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        rental = BookRental.objects.get(id=serializer.validated_data["id"])
        
        rental.status = "pending"
        rental.save()
        
        return Response(
            {
                "message": "Zwrot oczekuje na zatwierdzenie",
                "rental": {
                    "id": rental.id,
                    "status": rental.status,
                }
            },
            status=status.HTTP_200_OK
        )


class ExtendRentalPeriodView(APIView):
    """
    Widok umożliwiający przedłużenie okresu wypożyczenia.

        Funkcje:
        - Pozwala na jednorazowe przedłużenie wypożyczenia o 7 dni
        - Aktualizuje datę zwrotu
        - Oznacza wypożyczenie jako przedłużone

        Wymaga logowania i dostępu klienta.
    """
    permission_classes = [IsAuthenticated, IsCustomerPermission]

    # @schemas.extend_rental_customer_schema
    def post(self, request, *args, **kwargs):
        serializer = serializers.RentalIDSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        rental = BookRental.objects.get(id=serializer.validated_data["id"])
        
        if not rental.is_extended:
            rental.due_date += timedelta(days=7)
            rental.is_extended = True
            rental.save()
            return Response({"message": "Wypożyczenie przedłużone"}, status=status.HTTP_200_OK)
        
        return Response({"error": "Wypożyczenie zostało już przedłużone"}, status=status.HTTP_400_BAD_REQUEST)


class ListBooksView(ListAPIView):
    """
    Widok wyświetlający listę książek.

        Funkcje:
        - Wyświetla książki z liczbą dostępnych egzemplarzy
        - Umożliwia wyszukiwanie książek
        - Umożliwia filtrowanie książek po tytule, autorze lub kategorii

        Wymaga logowania.
    """

    permission_classes = [IsAuthenticated, IsCustomerPermission]
    serializer_class = serializers.ListBookSerializer

    # @schemas.list_books_customer_schema
    def get(self, request, *args, **kwargs):
        books = Book.objects.prefetch_related("copies").order_by("title")
        category_counts = Book.objects.values("category__name").annotate(count=Count("id"))
        
        serialized_books = self.get_serializer(books, many=True).data
        return Response({
            "books": serialized_books,
            "category_counts": category_counts
        }, status=status.HTTP_200_OK)


class DetailBookView(RetrieveAPIView):
    """
    Widok szczegółów książki.

        Funkcje:
        - Wyświetla informacje o konkretnej książce
        - Pokazuje opinie o książce
        - Umożliwia dodanie własnej opinii, jeżeli mamy lub mieliśmy wypożyczoną tę książkę
        - Umożliwia włączenie powiadomień

        Wymaga logowania.
    """
    permission_classes = [IsAuthenticated, IsCustomerPermission]
    serializer_class = serializers.BookDetailSerializer
    queryset = Book.objects.annotate(
        copies_available=Exists(BookCopy.objects.filter(book=OuterRef("pk"), is_available=True)),
        available_copies=Count("copies", filter=Q(copies__is_available=True))
    )


class SubscribeBookView(APIView):
    """
    Widok obsługujący subskrypcję powiadomień o książce.

        Funkcje:
        - Włącza powiadomienia o dostępności książki
        - Zapobiega wielokrotnemu dodaniu powiadomienia

        Wymaga logowania i dostępu klienta.
    """

    permission_classes = [IsAuthenticated, IsCustomerPermission]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            book = Book.objects.get(id=request.data["id"])
        except Book.DoesNotExist:
            return Response({"error": "Książka z tym id nie istnieje"}, status=status.HTTP_400_BAD_REQUEST)

        _, created = Notification.objects.get_or_create(
            user=user, book=book, is_available=False
        )

        if not created:
            return Response({"message": "Już masz włączone powiadomienia odnośnie tej książki"}, status=status.HTTP_200_OK)

        return Response({"message": "Powiadomienia włączone pomyślnie"}, status=status.HTTP_201_CREATED)


class DashboardEmployeeView(APIView):
    """
    Widok pulpitu pracownika.

        Funkcje:
        - Wyświetla statystyki wypożyczeń
        - Pokazuje listę użytkowników
        - Prezentuje najczęściej wypożyczane książki
        - Wyświetla powiadomienia

        Wymaga logowania i dostępu pracownika.
    """

    permission_classes = [IsAuthenticated, IsEmployeePermission]

    def get(self, request, *args, **kwargs):
        user = request.user

        most_rented_books = (
            BookRental.objects.values("book_copy__book__title")
            .annotate(rental_count=Count("id"))
            .order_by("-rental_count")[:3]
        )

        data = {
            "users_rented_books": list(
                BookRental.objects.filter(user=user, status="rented").values(
                    "id", "book_copy__book__title", "due_date"
                )
            ),
            "rented_books": list(
                BookRental.objects.filter(status="rented").values(
                    "id", "book_copy__book__title", "user__username", "due_date"
                )
            ),
            "rented_books_old": list(
                BookRental.objects.filter(user=user, status="returned").values(
                    "id", "book_copy__book__title", "due_date"
                )
            ),
            "notifications": list(
                Notification.objects.filter(
                    user=user, is_read=False, is_available=True
                ).values("id", "book__title", "created_at")
            ),
            "customers": list(
                CustomUser.objects.filter(is_employee=False).values("id", "username", "email")
            ),
            "all_users": list(CustomUser.objects.values("id", "username", "email")),
            "overdue_rentals": list(
                BookRental.objects.filter(status="overdue").values(
                    "id", "book_copy__book__title", "user__username", "due_date"
                )
            ),
            "most_rented_books": list(most_rented_books),
            "total_rentals": most_rented_books.aggregate(total=Sum("rental_count"))["total"]
            or 0,
            "returns_to_approve": list(
                BookRental.objects.filter(status="pending").values(
                    "id", "book_copy__book__title", "user__username"
                )
            ),
        }

        return Response(data, status=status.HTTP_200_OK)


class AddBookView(CreateAPIView):
    """
    Widok dodawania nowej książki.

        Funkcje:
        - Umożliwia wprowadzenie danych nowej książki
        - Tworzy nowe egzemplarze książki

        Wymaga logowania i dostępu pracownika.
    """

    permission_classes = [IsAuthenticated, IsEmployeePermission]

    def post(self, request, *args, **kwargs):
        serializer = serializers.AddBookSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        title = serializer.validated_data["title"]
        author = serializer.validated_data["author"]
        total_copies = serializer.validated_data["total_copies"]

        ai_description = get_ai_generated_description(title, author)

        book = Book.objects.create(title=title, author=author, description=ai_description)
        book_copies = [BookCopy(book=book) for _ in range(total_copies)]
        BookCopy.objects.bulk_create(book_copies)

        return Response({"message": "Pomyślnie dodano książkę"}, status=status.HTTP_201_CREATED)


class EditBookView(APIView):
    """
    Widok edycji książki.

        Funkcje:
        - Pozwala modyfikować dane książki
        - Obsługuje dodawanie i usuwanie egzemplarzy

        Wymaga logowania i dostępu pracownika.
    """

    permission_classes = [IsAuthenticated, IsEmployeePermission]

    def put(self, request, pk, *args, **kwargs):
        serializer = serializers.EditBookSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            book = Book.objects.get(id=serializer.validated_data["id"])
        except Book.DoesNotExist:
            return Response({"error": "Książka z tym id nie istnieje"}, status=status.HTTP_400_BAD_REQUEST)

        new_total_copies = serializer.validated_data["total_copies"]
        old_total_copies = book.copies.count()
        copies_difference = old_total_copies - new_total_copies

        book.title = serializer.validated_data["title"]
        book.author = serializer.validated_data["author"]
        book.save()

        if copies_difference > 0:
            available_copies = BookCopy.objects.filter(book=book, is_available=True)
            if copies_difference > available_copies.count():
                return Response(
                    {"error": f"Nie można usunąć {copies_difference} egzemplarzy. "
                                f"Dostępnych jest tylko {available_copies.count()}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            available_copies[:copies_difference].delete()
        elif copies_difference < 0:
            BookCopy.objects.bulk_create([BookCopy(book=book) for _ in range(abs(copies_difference))])

        return Response({"message": "Książka została zaktualizowana"}, status=status.HTTP_200_OK)


class DeleteBookView(APIView):
    """
    Widok usuwania książki.

        Funkcje:
        - Wyświetla potwierdzenie usunięcia
        - Usuwa książkę z systemu

        Wymaga logowania i dostępu pracownika.
    """
    permission_classes = [IsAuthenticated, IsEmployeePermission]

    def delete(self, request):
        try:
            book = Book.objects.get(id=request.data["id"])
        except Book.DoesNotExist:
            return Response({"error": "Książka z tym id nie istnieje"}, status=status.HTTP_400_BAD_REQUEST)
        book.delete()
        return Response({"message": "Książka została usunięta"}, status=status.HTTP_204_NO_CONTENT)


class ApproveReturnView(APIView):
    """
    API endpoint do zatwierdzania zwrotu książki.

        Funkcje:
        - Zmienia status wypożyczenia na "returned"
        - Aktualizuje dostępność egzemplarza książki
        - Wysyła powiadomienia do użytkownika

        Wymaga logowania i dostępu pracownika.
    """
    permission_classes = [IsAuthenticated, IsEmployeePermission]

    def post(self, request, pk):
        try:
            rental = BookRental.objects.get(id=request.data["id"])
        except BookRental.DoesNotExist:
            return Response({"error": "Zwrot z tym id nie istnieje"}, status=status.HTTP_400_BAD_REQUEST)

        rental.status = "returned"
        rental.return_date = date.today()
        rental.save()

        book_copy = rental.book_copy
        book_copy.is_available = True
        book_copy.borrower = None
        book_copy.save()

        book = rental.book_copy.book

        Notification.objects.filter(book=book.id, is_available=False).update(
            is_available=True,
            message=f"Książka {book.title} jest gotowa do wypożyczenia",
        )

        Notification.objects.create(
            user=rental.user,
            book=book,
            is_available=True,
            message=f"Zwrot książki {book.title} został zatwierdzony",
        )

        return Response(
            {"message": "Zwrot książki został zatwierdzony"}, status=status.HTTP_200_OK
        )


class ListBorrowsView(ListAPIView):
    """
    Widok listy wypożyczeń.

        Funkcje:
        - Wyświetla wszystkie wypożyczenia
        - Sortuje wypożyczenia według statusu

        Wymaga logowania i dostępu pracownika.
    """

    permission_classes = [IsAuthenticated, IsEmployeePermission]
    serializer_class = serializers.BookRentalSerializer

    def get_queryset(self):
        status_order = Case(
            When(status="rented", then=Value(1)),
            When(status="overdue", then=Value(2)),
            When(status="returned", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )

        return BookRental.objects.annotate(status_priority=status_order).order_by(
            "status_priority", "-rental_date"
        )


class ListUsersView(ListAPIView):
    """
    Widok listy użytkowników.

        Funkcje:
        - Wyświetla wszystkich użytkowników systemu

        Wymaga logowania i dostępu pracownika.
    """

    permission_classes = [IsAuthenticated, IsEmployeePermission]
    serializer_class = serializers.CustomUserSerializer
    queryset = CustomUser.objects.all()


class DetailUserView(RetrieveAPIView):
    """
    Widok szczegółów użytkownika.

        Funkcje:
        - Wyświetla szczegółowe informacje o użytkowniku

        Wymaga logowania i dostępu pracownika.
    """
    
    permission_classes = [IsAuthenticated, IsEmployeePermission]
    queryset = CustomUser.objects.all()
    serializer_class = serializers.CustomUserSerializer

    def get_object(self):
        return self.request.user

class EditUserView(UpdateAPIView):
    """
        Widok edycji użytkownika.

        Funkcje:
        - Umożliwia modyfikację danych użytkownika
        - Przekierowuje do odpowiedniego pulpitu po zapisie

        Wymaga logowania.
    """

    permission_classes = [IsAuthenticated, IsEmployeePermission]
    queryset = CustomUser.objects.all()
    serializer_class = serializers.EditUserSerializer

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = serializer.save()
        if user.is_employee:
            return reverse("dashboard_employee", kwargs={"pk": user.id})
        else:
            return reverse("dashboard_client", kwargs={"pk": user.id})


class ActiveUserView(APIView):
    """
    Widok zmiany statusu aktywności użytkownika.

        Funkcje:
        - Włącza/wyłącza konto użytkownika

        Wymaga logowania i dostępu administratora.
    """
    permission_classes = [IsAuthenticated, IsEmployeePermission]

    def post(self, request):
        user = CustomUser.objects.get(id=request.data["id"])
        user.is_active = not user.is_active
        user.save()
        return Response({"message": "User status changed."}, status=status.HTTP_200_OK)


class DeleteUserView(APIView):
    """
    Widok usuwania użytkownika.

        Funkcje:
        - Wyświetla potwierdzenie usunięcia
        - Usuwa użytkownika z systemu

        Wymaga logowania i dostępu administratora.
    """
    permission_classes = [IsAuthenticated, IsEmployeePermission]

    def post(self, request):
        user = CustomUser.objects.get(id=request.data["id"])
        user.delete()

        return Response({"message": "User deleted"}, status=status.HTTP_200_OK)


class AddUserView(CreateAPIView):
    """
    Widok dodawania nowego użytkownika.

    Funkcje:
    - Umożliwia utworzenie nowego konta użytkownika

    Wymaga logowania i dostępu administratora.
    """

    queryset = CustomUser
    serializer_class = serializers.AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdminPermission]


class UserRegistrationView(CreateAPIView):
    """
        Widok rejestracji użytkownika.

        Funkcje:
        - Wyświetla formularz rejestracji
        - Przekierowuje zalogowanych użytkowników
    """

    serializer_class = serializers.UserSerializer
    permission_classes = [AllowAny]
