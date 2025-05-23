import django.contrib.auth.password_validation as validators
from django.core.exceptions import ValidationError
from rest_framework import serializers
from datetime import datetime
from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import Book, Category

from books.models import Badge, Book, BookCopy, BookRental, Category, Notification, Opinion
from books.models import CustomUser


class ListBookSerializer(serializers.ModelSerializer):
    available_copies = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "category",
            "description",
            "available_copies",
        ]

    def get_available_copies(self, obj):
        return obj.copies.filter(is_available=True).count()




class AddBookSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    published_date = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])

    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "category",
            "published_date",
            "isbn",
            "total_copies",
        ]
        

class EditBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "category",
            "isbn",
            "total_copies",
            "description",
            "published_date",
        ]
        

class EditUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "phone")


class OpinionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Opinion
        fields = ("rate", "comment")


class BookRentalSerializer(serializers.ModelSerializer):
    rentalId = serializers.IntegerField(source="id", read_only=True)
    notificationId = serializers.IntegerField(source="id", read_only=True)
    book_title = serializers.CharField(source="book_copy.book.title", read_only=True)
    book_author = serializers.CharField(source="book_copy.book.author", read_only=True)

    class Meta:
        model = BookRental
        fields = [
            "rentalId",
            "notificationId",
            "book_title",
            "book_author",
            "rental_date",
            "due_date",
            "return_date",
            "is_extended",
            "status",
            "fine",
        ]


class NotificationSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Notification
        fields = ["message", "is_read", "book_title", "created_at"]


class OpinionSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Opinion
        fields = ["book_title", "rate", "comment", "created_at"]


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = [
            "id",
            "first_book",
            "ten_books",
            "twenty_books",
            "hundred_books",
            "three_categories",
        ]


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "username",
            "first_name",
            "last_name",
            "password",
            "email",
            "phone",
            "is_employee",
            "is_active",
        ]

    def create(self, validated_data):
        user = CustomUser(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user

class UserRegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ("username", "password")

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


class BookDetailSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name')
    
    class Meta:
        model = Book
        fields = ["title", "author", "category", "description", 
                  "published_date", "isbn", "total_copies",]

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "first_name", "last_name", "phone", "is_active"]

class ListUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "first_name", "last_name", "phone", "is_active"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]