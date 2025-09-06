from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("packages/", views.package_view, name="packages"),
    path("invest/", views.invest_view, name="invest"),
    path("success/", views.investment_success, name="investment_success"),
    path("my-investments/", views.investment_record, name="my_investments"),
    path("buy/", views.buy_view, name="buy"),
    path("updatepassword/", views.change_password, name="update_password"),
    path("withdraw", views.withdraw_view, name="withdraw"),
]
