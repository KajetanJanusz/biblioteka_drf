from django.db.models.signals import post_save
from django.dispatch import receiver
from books.models import BookRental, CustomUser, Badge


@receiver(post_save, sender=CustomUser)
def create_user_badge(sender, instance, created, **kwargs):
    if created:
        Badge.objects.create(user=instance)


@receiver(post_save, sender=BookRental)
def update_user_badges(sender, instance, created, **kwargs):
    """Aktualizuje odznaki użytkownika po utworzeniu wypożyczenia"""
    if created:
        user = instance.user
        badge, _ = Badge.objects.get_or_create(user=user)

        rented_books = BookRental.objects.filter(user=user).count()

        categories_read = (
            BookRental.objects.filter(user=user)
            .values("book_copy__book__category")
            .distinct()
            .count()
        )

        if rented_books >= 1 and not badge.first_book:
            badge.first_book = True

        if rented_books >= 10 and not badge.ten_books:
            badge.ten_books = True

        if rented_books >= 20 and not badge.twenty_books:
            badge.twenty_books = True

        if rented_books >= 100 and not badge.hundred_books:
            badge.hundred_books = True

        if categories_read >= 3 and not badge.three_categories:
            badge.three_categories = True

        badge.save()
