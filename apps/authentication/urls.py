from django.urls import path
from .views import login_view, register_user, fill_profile
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path('profile/create/', fill_profile, name="fill_profile"),
    path('profile/create/send', fill_profile, name="send_profile_infos"),
    path('logout/', LogoutView.as_view(), name="logout")
]
