from django.urls import path
from apps.users.views import UsernameCount
from apps.users.views import MobileCount
from apps.users.views import RegisterView, LoginView, LogoutView

urlpatterns = [
    # 判断用户名是否重复
    path('usernames/<username_converter:username>/count/', UsernameCount.as_view()),
    path('mobiles/<mobile_converter:mobile>/count/', MobileCount.as_view()),
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
]
