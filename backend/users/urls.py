from django.urls import path
from .views import register_user, user_profile, logout_user

urlpatterns = [
    path('register/', register_user, name='register'),
    path('profile/', user_profile, name='profile'),
    path('logout/', logout_user, name='logout'),
]
