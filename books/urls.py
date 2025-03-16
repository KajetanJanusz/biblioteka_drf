from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from books import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", views.UserRegistrationView.as_view(), name="register"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"
    ),
    path(
        "dashboard/customer/",
        views.DashboardCustomerView.as_view(),
        name="dashboard_customer",
    ),
    path(
        "dashboard/employee/",
        views.DashboardEmployeeView.as_view(),
        name="dashboard_employee",
    ),
    path("users/", views.ListUsersView.as_view(), name="list_users"),
    path("users/details/", views.DetailUserView.as_view(), name="detail_user"),
    path("users/add", views.AddUserView.as_view(), name="add_user"),
    path("users/edit", views.EditUserView.as_view(), name="edit_user"),
    path("users/delete", views.DeleteUserView.as_view(), name="delete_user"),
    path("users/active", views.ActiveUserView.as_view(), name="active_user"),
    path("articles/", views.ArticlesView.as_view(), name="articles"),
    path("borrows/", views.ListBorrowsView.as_view(), name="list_borrows"),
    path("books/", views.ListBooksView.as_view(), name="list_books"),
    path("books/details/", views.DetailBookView.as_view(), name="detail_book"),
    path("books/add/", views.AddBookView.as_view(), name="add_book"),
    path("books/edit/", views.EditBookView.as_view(), name="edit_book"),
    path("books/delete/", views.DeleteBookView.as_view(), name="delete_book"),
    path("books/borrow/", views.BorrowBookView.as_view(), name="borrow_book"),
    path("books/return/", views.ReturnBookView.as_view(), name="return_book"),
    path(
        "books/extend/",
        views.ExtendRentalPeriodView.as_view(),
        name="extend_book",
    ),
    path(
        "books/approve-return/",
        views.ApproveReturnView.as_view(),
        name="approve_return",
    ),
    path(
        "books/mark-as-read/",
        views.MarkNotificationAsReadView.as_view(),
        name="mark_as_read",
    ),
    path(
        "books/notification",
        views.SubscribeBookView.as_view(),
        name="subscribe_book",
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
