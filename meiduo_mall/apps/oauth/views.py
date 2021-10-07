from django.shortcuts import render

# Create your views here.

"""
第三方登录的步骤：
1. QQ互联开发平台申请成为开发者（可以不用做）
2. QQ互联创建应用（可以不用做）
3. 按照文档开发（看文档的）



3.1 准备工作

    # QQ登录参数
    # 我们申请的客户端id
    QQ_CLIENT_ID = '101474184' appid
    # 我们申请的客户端秘钥
    QQ_CLIENT_SECRET = 'c6ce949e04e12ecc909ae6a8b09b637c' appkey
    # 我们申请时添加的:登录成功后回调的路径
    QQ_REDIRECT_URI = 'http://www.meiduo.site:8080/oauth_callback.html'


3.2 放置QQ登录的图标(目的:让我们点击QQ图标来实现第三方登录)

3.3 根据oauth2.0 来获取code和token
    对于应用而言，需要进行两步：
    1. 获取Authorization Code;表面是一个链接，实质是需要用户同意，然后获取code

    2. 通过Authorization Code获取Access Token

3.4 通过token换取openid
    openid是此网站上唯一对应用户身份的标识，网站可将此ID进行存储便于用户下次登录时辨识其身份，
    或将其与用户在网站上的原有账号进行绑定。

把openid 和 用户信息 进行一一对应的绑定


生成用户绑定链接-->获取code-->获取token-->获取openid-->保存openid

"""

"""
生成用户绑定链接

前端： 当用户点击QQ登录图标的时候，前端应该发送一个axios(Ajax)请求

后端：
    请求
    业务逻辑        调用QQLoginTool 生成跳转链接
    响应            返回跳转链接 {"code":0,"qq_login_url":"http://xxx"}
    路由          GET   qq/authorization/
    步骤      
            1. 生成 QQLoginTool 实例对象
            2. 调用对象的方法生成跳转链接
            3. 返回响应

404 路由不匹配
405 方法不被允许（你没有实现请求对应的方法）
"""

from meiduo_mall import settings
from django.http import HttpRequest, JsonResponse
from django.views import View
from QQLoginTool.QQtool import OAuthQQ


class QQLoginURLView(View):
    def get(self, request):
        # 1. 生成 QQLoginTool 实例对象
        # client_id=None, appid
        # client_secret=None, appsecret
        # redirect_uri=None, 用户同意登录之后，跳转的页面
        # state=None,
        qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                     client_secret=settings.QQ_CLIENT_SECRET,
                     redirect_uri=settings.QQ_REDIRECT_URI,
                     state='xxxxx')
        # 2. 调用对象的方法生成跳转链接
        qq_login_url = qq.get_qq_url()
        # 3. 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'login_url': qq_login_url})


"""
需求： 获取code，通过code换取token，再通过token换取openid

前端：
        应该获取 用户同意登录的code。把这个code发送给后端
后端：
    请求         获取code
    业务逻辑      通过code换取token，再通过token换取openid
                根据openid进行判断
                如果没有绑定过，则需要绑定
                如果绑定过，则直接登录
    响应          
    路由         GET  oauth_callback/?code=xxxxx
    步骤
        1. 获取code
        2. 通过code换取token
        3. 再通过token换取openid
        4. 根据openid进行判断
        5. 如果没有绑定过，则需要绑定
        6. 如果绑定过，则直接登录
"""
"""
需求： 绑定账号信息
    QQ(openid) 和 美多的账号信息

前端：
        当用户输入 手机号，密码，短信验证码之后就发送axios请求。请求需要携带 mobile,password,sms_code,access_token(openid)
后端：

    请求： 接收请求，获取请求参数
    业务逻辑： 绑定，完成状态保持
    响应：  返回code=0 跳转到首页
    路由：  POST   oauth_callback/
    步骤：
            1. 接收请求
            2. 获取请求参数  openid
            3. 根据手机号进行用户信息的查询
            4. 查询到用户手机号已经注册了。判断密码是否正确,密码正确就可以直接保存（绑定） 用户和openid信息
            5. 查询到用户手机号没有注册。我们就创建一个user信息,然后再绑定
            6. 完成状态保持
            7. 返回响应

"""
from apps.oauth.models import OAuthQQUser
from django.contrib.auth import login
from django_redis import get_redis_connection
from apps.users.models import User
import json
import re


class OauthQQView(View):
    def get(self, request):
        # 1. 获取code
        code = request.GET.get('code')
        if code is None:
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})

        # 2. 通过code换取token
        qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                     client_secret=settings.QQ_CLIENT_SECRET,
                     redirect_uri=settings.QQ_REDIRECT_URI,
                     state='xxxxx')
        token = qq.get_access_token(code)

        # 3. 再通过token换取openid
        openid = qq.get_open_id(token)

        # 4. 根据openid进行判断
        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 5. 如果没有绑定过，则需要绑定
            response = JsonResponse({'code': 400, 'access_token': openid})
            return response
        else:
            # 6. 如果绑定过，则直接登录
            # 设置session
            login(request, qquser.user)
            # 设置cookie
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('username', qquser.user)
            return response

    def post(self, request):
        # 1. 接收请求
        data = json.loads(request.body.decode())

        # 2. 获取请求参数  openid
        mobile = data.get('mobile')
        password = data.get('password')
        sms_code = data.get('sms_code')
        openid = data.get('access_token')

        # 参数验证
        if not all([mobile, password, sms_code]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})
        if not re.match('1[3-9][0-9]{9}', mobile):
            return JsonResponse({'code': 400, 'errmsg': '手机号不满足规则'})
        if not re.match('[a-zA-Z0-9]{8,20}', password):
            return JsonResponse({'code': 400, 'errmsg': '密码不满足规则'})

        redis_cli = get_redis_connection('code')
        redis_sms_code = redis_cli.get(mobile)
        if not redis_sms_code:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码失败'})
        if redis_sms_code.decode().lower() != sms_code:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码错误'})

        # 3. 根据手机号进行用户信息的查询
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 5. 查询到用户手机号没有注册,我们就创建一个user信息,然后再绑定
            user = User.objects.create_user(username=mobile, mobile=mobile, password=password)

        else:
            # 4. 查询到用户手机号已经注册了,判断密码是否正确,密码正确就可以直接保存(绑定)用户和openid信息
            if not user.check_password(password):
                return JsonResponse({'code': 400, 'errmsg': '账号或密码错误'})

        OAuthQQUser.objects.create(user=user, openid=openid)

        # 6. 完成状态保持
        login(request, user)

        # 7. 返回响应
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})

        response.set_cookie('username', user.username)

        return response
