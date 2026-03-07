from django.urls import path
from accounts.views.login import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenLogoutView,
)
from accounts.views.user import UpdateUserView, UserView
from accounts.views.user import ChangePasswordView


urlpatterns = [
    path("auth/login", CustomTokenObtainPairView.as_view(), name="login"),
    path("auth/logout", CustomTokenLogoutView.as_view(), name="logout"),
    path("auth/token/refresh", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("account/me", UserView.as_view(), name="get_me"),
    path(
        "account/change-password", ChangePasswordView.as_view(), name="change_password"
    ),
    path("account/update", UpdateUserView.as_view(), name="update_user"),
]
