from django.shortcuts import render

# Create your views here.
"""
需求分析:根据页面功能,功能要求与后端相结合
1. 经验
2. 关注类似网站相识功能
"""

"""
判断用户是否重复的功能

前端: 当用户输入用户名之后,失去焦点,发送一个axios(ajax)请求

后端:
    请求: 接受用户名
    业务逻辑: 如果查询为0,则没有注册
             如果查询为1,则有注册
    响应: JSON(code:0,count:0/1,errmsg:ok)
    路由: usernames/(?P<username>[a-zA-Z0-9_-]{5-20})/count/
"""
from django.views import View
from apps.users.models import User
from django.http import JsonResponse


class UsernameCount(View):
    def get(self, request, username):
        # 1.获取用户名
        # 2.查询数据
        count = User.objects.filter(username=username).count()
        # 3.返回响应
        return JsonResponse({'code': 0, 'count': count, 'errmsg': 'ok'})
