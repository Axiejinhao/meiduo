from django.contrib.auth import login
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
import re


class UsernameCount(View):
    def get(self, request, username):
        # 1.获取用户名,对用户名进行判断
        # if not re.match('[a-zA-Z0-9_-]{5,20}', username):
        #     return JsonResponse({'code': 200, 'errmsg': '用户名不满足条件'})
        # 2.查询数据
        count = User.objects.filter(username=username).count()
        # 3.返回响应
        return JsonResponse({'code': 0, 'count': count, 'errmsg': 'ok'})


class MobileCount(View):
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'code': 0, 'count': count, 'errmsg': 'ok'})


"""
注册

前端: 当用户输入用户名,密码,确认密码,手机号,是否同意协议后,点击注册按钮
      前端会发送axios请求
后端:
    请求: 接受请求,获取数据
    业务逻辑: 验证数据,数据入库
    响应: JSON(code:0,count:0/1,errmsg:ok)
          响应码 0:成功,400:失败
    路由: POST register/
    步骤:
    # 1. 接受请求
    # 2. 获取数据
    # 3. 验证数据
    #     3.1 用户名,密码,确认密码,手机号,是否同意协议后都需要
    #     3.2 用户名满足规则,不能重复
    #     3.3 密码满足规则
    #     3.4 密码和确认密码一致
    #     3.5 手机号满足规则,不能重复
    #     3.6 需要统一协议
    # 4. 数据入库
    # 5. 返回响应
"""
import json


class RegisterView(View):
    def post(self, request):
        # 1. 接受请求
        body_bytes = request.body
        body_str = body_bytes.decode()
        body_dict = json.loads(body_str)

        # 2. 获取数据
        username = body_dict.get('username')
        password = str(body_dict.get('password'))
        password2 = str(body_dict.get('password2'))
        mobile = str(body_dict.get('mobile'))
        allow = body_dict.get('allow')

        # 3. 验证数据
        #     3.1 用户名,密码,确认密码,手机号,是否同意协议后都需要
        if not all([username, password, password2, mobile, allow]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})
        #     3.2 用户名满足规则,不能重复
        if not re.match('[a-zA-Z0-9_-]{5,20}', username):
            return JsonResponse({'code': 400, 'errmsg': '用户名不满足规则'})
        #     3.3 密码满足规则
        if not re.match('[a-zA-Z0-9]{8,20}', password):
            return JsonResponse({'code': 400, 'errmsg': '密码不满足规则'})
        #     3.4 密码和确认密码一致
        if password != password2:
            return JsonResponse({'code': 400, 'errmsg': '密码和确认密码不相同'})
        #     3.5 手机号满足规则,不能重复
        if not re.match('1[3-9][0-9]{9}', mobile):
            return JsonResponse({'code': 400, 'errmsg': '手机号不满足规则'})
        #     3.6 需要同意协议
        if not allow:
            return JsonResponse({'code': 400, 'errmsg': '必须同意协议'})
        # 4. 数据入库
        # User.objects.create(username=username, password=password, mobile=mobile)
        user = User.objects.create_user(username=username, password=password, mobile=mobile)

        # 状态保持,登录用户的状态保持
        # user是已经登录的用户信息
        login(request, user)

        # 5. 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


"""
注册成功,已经登录
注册成功,再次登录
客户端cookie,服务端session
"""
