from django.urls import path

from .views import DocumentedTokenRefreshView, MeView, ThrottledTokenObtainPairView

urlpatterns = [
    path("auth/token/", ThrottledTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", DocumentedTokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
]
