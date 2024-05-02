from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path('request-password-reset/', request_reset_password, name="reset_password"),
    path('reset-password/<str:token>', reset_password_validation, name="reset_password_token"),
    path('reset-password/', reset_password_page, name="reset_password_page"),

    path('profile/create/', fill_profile, name="fill_profile"),
    path('profile/create/send', fill_profile, name="send_profile_infos"),

    path('validate/<str:token>', validate_email, name='confirm_email'),
    path('resend-confirmation/', reconfirm_email, name='resend_confirmation'),

    path('logout/', LogoutView.as_view(), name="logout"),
]
