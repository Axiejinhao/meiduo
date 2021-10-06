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
from django_redis import get_redis_connection


class RegisterView(View):
    def post(self, request):
        # 1. 接受请求
        body_bytes = request.body
        body_str = body_bytes.decode()
        body_dict = json.loads(body_str)

        # 2. 获取数据
        username = body_dict.get('username')
        password = body_dict.get('password')
        password2 = body_dict.get('password2')
        mobile = body_dict.get('mobile')
        allow = body_dict.get('allow')
        sms_code = body_dict.get('sms_code').lower()

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

        #     3.7 验证短信
        redis_cli = get_redis_connection('code')
        redis_sms_code = redis_cli.get(mobile)
        if not redis_sms_code:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码失败'})
        if redis_sms_code.decode().lower() != sms_code:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码错误'})

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

"""
登录

前端：当用户把用户名和密码输入完成之后，会点击登录按钮。这个时候前端应该发送一个axios请求

后端：
    请求 接收数据，验证数据
    业务逻辑 验证用户名和密码是否正确，session
    响应 返回JSON数据 0 成功,400 失败
    POST /login/
    
步骤：
    1. 接收数据
    2. 验证数据
    3. 验证用户名和密码是否正确
    4. session
    5. 判断是否记住登录
    6. 返回响应

"""

from django.contrib.auth import authenticate
from django.contrib.auth import login


class LoginView(View):
    def post(self, request):
        # 1. 接收数据
        data = json.loads(request.body.decode())
        username = data.get('username')
        password = data.get('password')
        remembered = data.get('remembered')

        # 2. 验证数据
        if not all([username, password]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})

        # 3. 验证用户名和密码是否正确
        # 通过用户名查询数据库
        # User.objects.filter(username=username)

        # authenticate传递用户名和密码
        # 如果用户名和密码正确,返回User信息,否则返回None
        user = authenticate(username=username, password=password)

        if user is None:
            return JsonResponse({'code': 400, 'errmsg': '账户或密码错误'})

        # 4. session
        login(request, user)

        # 5. 判断是否记住登录
        if remembered:
            request.session.set_expiry(3600 * 12)
        else:
            request.session.set_expiry(0)

        # 6. 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})
