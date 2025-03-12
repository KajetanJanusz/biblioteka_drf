import django.contrib.auth.password_validation as validators
from django.core.exceptions import ValidationError
from rest_framework import serializers

from books.models import Badge, Book, BookCopy, BookRental, Notification, Opinion
from books.models import CustomUser


class ListBookSerializer(serializers.ModelSerializer):
    available_copies = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ["id", "title", "author", "category", "description", "available_copies"]
    
    def get_available_copies(self, obj):
        return obj.copies.filter(is_available=True).count()

class AddBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id", 
            "title",
            "author",
            "category",
            "published_date",
            "isbn",
            "total_copies",
        ]

class BookCopySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCopy
        fields = ["id", "book", "is_available", "borrower"]

class EditBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "category", "isbn", "total_copies", "description"]
        
class BorrowBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id']
        
    def validate_book_id(self, value):
        try:
            book = Book.objects.get(id=value)
        except Book.DoesNotExist:
            raise serializers.ValidationError("Książka o podanym ID nie istnieje.")
        
class RentalIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookRental
        fields = ['id']
        
    def validate_rental_id(self, value):
        try:
            rental = BookRental.objects.get(id=value)
        except BookRental.DoesNotExist:
            raise serializers.ValidationError("Wypożyczenie o podanym ID nie istnieje.")
        
        
class EditUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "first_name", "last_name", "phone")


class OpinionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Opinion
        fields = ("id", "rate", "comment")


class BookRentalSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book_copy.book.title', read_only=True)
    book_author = serializers.CharField(source='book_copy.book.author', read_only=True)
    
    class Meta:
        model = BookRental
        fields = [
            "id", 
            'book_title', 
            'book_author', 
            'rental_date', 
            'due_date', 
            'return_date', 
            'is_extended', 
            'status',
            'fine'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'message', 
            'is_read', 
            'book_title',
            'created_at'
        ]


class OpinionSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    
    class Meta:
        model = Opinion
        fields = [
            "id", 
            'book_title', 
            'rate', 
            'comment', 
            'created_at'
        ]

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = [
            "id", 
            'first_book', 
            'ten_books', 
            'twenty_books', 
            'hundred_books', 
            'three_categories'
        ]


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id", 
            "username",
            "first_name",
            "last_name",
            "password",
            "email",
            "phone",
            "is_employee",
            "is_active",
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
        return user
    
    
class MarkReadNotificationAsReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "id"


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ("id", "username", "password")

    def validate(self, data):
        password = data.get("password")
        try:
            validators.validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({"error": e.messages}) from e
        return data

    def create(self, validated_data):
        return CustomUser.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
        )

from rest_framework import serializers
from .models import Book, Opinion

class BookDetailSerializer(serializers.ModelSerializer):
    opinions = serializers.SerializerMethodField()
    copies_available = serializers.BooleanField()
    available_copies = serializers.IntegerField()
    can_add_opinion = serializers.SerializerMethodField()
    notifications_enabled = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = (
            'id',
            'title',
            'author',
            'description',
            'opinions',
            'copies_available',
            'available_copies',
            'can_add_opinion',
            'notifications_enabled',
        )

    def get_opinions(self, obj):
        # Assuming you want to return a list of opinions related to this book
        opinions = Opinion.objects.filter(book=obj)
        return OpinionSerializer(opinions, many=True).data

    def get_can_add_opinion(self, obj):
        # Logic to determine if the user can add an opinion
        user = self.context.get('request').user
        return user.has_borrowed_book(obj)

    def get_notifications_enabled(self, obj):
        # Logic to check if notifications are enabled for the user
        user = self.context.get('request').user
        return user.notifications_enabled


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "first_name", "last_name"]