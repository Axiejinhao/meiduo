from django.urls import path
from apps.users.views import UsernameCount
from apps.users.views import MobileCount
from apps.users.views import RegisterView, LoginView, LogoutView
from apps.users.views import CenterView, EmailView
from apps.users.views import EmailVerifyView
from apps.users.views import AddressCreateView, AddressView
from apps.users.views import UpdateDestroyAddressView

urlpatterns = [
    # 判断用户名是否重复
    path('usernames/<username_converter:username>/count/', UsernameCount.as_view()),
    path('mobiles/<mobile_converter:mobile>/count/', MobileCount.as_view()),
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('info/', CenterView.as_view()),
    path('emails/', EmailView.as_view()),
    path('emails/verification/', EmailVerifyView.as_view()),
    path('addresses/create/', AddressCreateView.as_view()),
    path('addresses/', AddressView.as_view()),
    path('addresses/<address_id>/', UpdateDestroyAddressView.as_view()),
]
