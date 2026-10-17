from rest_framework.pagination import CursorPagination


class PaymentCursorPagination(CursorPagination):
    page_size = 20
    ordering = "-id"
