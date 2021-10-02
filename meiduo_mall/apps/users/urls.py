from django.urls import path
from apps.users.views import UsernameCount

urlpatterns = [
    # 判断用户名是否重复
    path('usernames/<username>/count/', UsernameCount.as_view()),
]
