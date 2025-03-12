# from books import serializers
# from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse, inline_serializer
# from drf_spectacular.types import OpenApiTypes

# dashboard_client_schema = extend_schema(
#     methods=["GET"],
#     description="Retrieve personalized dashboard information for the logged-in client. This includes rented books, unread notifications, user opinions, book recommendations, and more.",
#     summary="Client Dashboard",
#     tags=["Dashboard", "Client"],
#     responses={
#         200: {
#             "message": "str",
#             "description": "Personalized dashboard information for the client.",
#             "example": {
#                 "username": "johndoe",
#                 "rented_books": [
#                     {"id": 1, "book_title": "Book 1", "rental_date": "2025-03-01", "status": "rented"}
#                 ],
#                 "rented_books_old": [
#                     {"id": 2, "book_title": "Book 2", "rental_date": "2024-12-15", "status": "returned"}
#                 ],
#                 "notifications": [
#                     {"id": 1, "message": "You have an overdue book!", "is_read": False, "book_title": "Book 1", "created_at": "2025-03-05"}
#                 ],
#                 "opinions": [
#                     {"id": 1, "rate": 4, "comment": "Great book!", "book_title": "Book 1", "created_at": "2025-02-10"}
#                 ],
#                 "ai_recommendations": [
#                     {"book_title": "Recommended Book 1", "author": "Author 1"},
#                     {"book_title": "Recommended Book 2", "author": "Author 2"}
#                 ],
#                 "badges": {
#                     "id": 1,
#                     "first_book": True,
#                     "ten_books": False,
#                     "twenty_books": True,
#                     "hundred_books": False,
#                     "three_categories": True
#                 },
#                 "average_user_rents": 5,
#                 "all_my_rents": 15,
#                 "books_in_categories": [
#                     {"category": "Science Fiction", "count": 5},
#                     {"category": "Fantasy", "count": 3}
#                 ]
#             },
#         },
#         400: {
#             "error": "str",
#             "description": "Invalid request or missing information.",
#             "example": {"error": "Invalid user ID."}
#         },
#         429: {
#             "description": "Too many requests.",
#             "example": {"detail": "Request was throttled. Expected available in x seconds."}
#         },
#     },
# )

# articles_view_customer_schema = extend_schema(
#     methods=["GET"],
#     description="Retrieve a list of five articles related to books. This endpoint requires authentication for customers.",
#     summary="Book Articles (Customer)",
#     tags=["Customer"],
#     responses={
#         200: {
#             "message": "str",
#             "description": "A list of articles related to books.",
#             "example": {
#                 "articles": [
#                     {"id": 1, "title": "Article 1", "content": "This is an article about books."},
#                     {"id": 2, "title": "Article 2", "content": "Another insightful article about literature."},
#                     {"id": 3, "title": "Article 3", "content": "Discover new books to read."},
#                     {"id": 4, "title": "Article 4", "content": "Book review: A must-read novel."},
#                     {"id": 5, "title": "Article 5", "content": "Exploring the world of fantasy books."}
#                 ]
#             },
#         },
#         400: {
#             "error": "str",
#             "description": "Invalid request or missing information.",
#             "example": {"error": "Unable to fetch articles."}
#         },
#     },
# )


# mark_notification_as_read_customer_schema = extend_schema(
#     methods=["POST"],
#     description="Mark a notification as read. This endpoint requires authentication and customer permissions.",
#     summary="Mark Notification as Read (Customer)",
#     tags=["Customer"],
#     request=serializers.MarkReadNotificationAsReadSerializer,
#     responses={
#         200: {
#             "message": "str",
#             "description": "Notification marked as read successfully.",
#             "example": {"message": "Odczytane."},
#         },
#         400: {
#             "error": "str",
#             "description": "Invalid ID or failed to mark notification.",
#             "example": {"error": "Niepoprawne id."},
#         },
#     },
# )

# borrow_book_customer_schema = extend_schema(
#     methods=["POST"],
#     description="This endpoint handles the process of borrowing a book. It checks book availability, limits user rentals to 3, creates a new rental, and updates the book's copy status. Requires authentication and customer permissions.",
#     summary="Borrow Book (Customer)",
#     tags=["Customer"],
#     request=serializers.BorrowBookSerializer,
#     responses={
#         201: {
#             "message": "str",
#             "rental": {
#                 "book_title": "str",
#                 "rental_date": "date",
#                 "due_date": "date",
#                 "status": "str",
#                 "status_display": "str",
#             },
#             "description": "Book successfully borrowed.",
#             "example": {
#                 "message": "Książka wypożyczona",
#                 "rental": {
#                     "book_title": "Book Title",
#                     "rental_date": "2025-03-10",
#                     "due_date": "2025-04-09",
#                     "status": "rented",
#                     "status_display": "Rented",
#                 },
#             },
#         },
#         400: {
#             "error": "str",
#             "description": "Error response indicating an issue with the borrowing process.",
#             "example": {"error": "Nie ma wolnych egzemplarzy"},
#         },
#     },
# )


# return_book_customer_schema = extend_schema(
#     methods=["POST"],
#     description="This endpoint handles the book return process. It changes the rental status to 'pending' (awaiting approval), returns a confirmation message, and updates notifications. Requires authentication and customer permissions.",
#     summary="Return Book (Customer)",
#     tags=["Customer"],
#     request=serializers.RentalIDSerializer,
#     responses={
#         200: {
#             "message": "str",
#             "rental": {
#                 "id": "int",
#                 "status": "str",
#             },
#             "description": "Book return awaiting approval.",
#             "example": {
#                 "message": "Zwrot oczekuje na zatwierdzenie",
#                 "rental": {
#                     "id": 123,
#                     "status": "pending",
#                 },
#             },
#         },
#         400: {
#             "error": "str",
#             "description": "Error response indicating an issue with the return process.",
#             "example": {"error": "Invalid rental ID."},
#         },
#     },
# )


# extend_rental_customer_schema = extend_schema(
#     methods=["POST"],
#     description="This endpoint allows a user to extend their book rental period by 7 days. It updates the due date and marks the rental as extended. Only one extension is allowed per rental. Requires authentication and customer permissions.",
#     summary="Extend Rental Period (Customer)",
#     tags=["Customer"],
#     request=serializers.RentalIDSerializer,
#     responses={
#         200: {
#             "message": "str",
#             "description": "Book rental period successfully extended.",
#             "example": {"message": "Wypożyczenie przedłużone"},
#         },
#         400: {
#             "error": "str",
#             "description": "Error response indicating the rental cannot be extended.",
#             "example": {"error": "Wypożyczenie zostało już przedłużone"},
#         },
#     },
# )

# list_books_customer_schema = extend_schema(
#     methods=["GET"],
#     description="This endpoint returns a list of books along with the available copies and categories. It allows searching and filtering by title, author, or category. Requires authentication and customer permissions.",
#     summary="List Books (Customer)",
#     tags=["Customer"],
#     responses={
#         200: {
#             "books": "array",
#             "category_counts": "array",
#             "description": "List of books with available copies and category counts.",
#             "example": {
#                 "books": [
#                     {"title": "Book Title", "author": "Author Name", "category": "Category Name", "copies": 5}
#                 ],
#                 "category_counts": [{"category": "Category Name", "count": 10}]
#             },
#         }
#     },
# )


# detail_book_customer_schema = extend_schema(
#     methods=["GET"],
#     description="This endpoint returns detailed information about a specific book, including its availability, user reviews, and options to add a review and enable notifications if the book has been or is currently rented. Requires authentication and customer permissions.",
#     summary="Detail Book (Customer)",
#     tags=["Customer"],
#     responses={
#         200: {
#             "book": "object",
#             "reviews": "array",
#             "can_add_review": "boolean",
#             "notifications_enabled": "boolean",
#             "description": "Details about the book, including reviews and availability status.",
#             "example": {
#                 "book": {
#                     "title": "Book Title",
#                     "author": "Author Name",
#                     "category": "Category Name",
#                     "available_copies": 3,
#                     "copies_available": True
#                 },
#                 "reviews": [
#                     {"user": "Username", "rating": 5, "comment": "Great book!"}
#                 ],
#                 "can_add_review": True,
#                 "notifications_enabled": False
#             },
#         }
#     },
# )
