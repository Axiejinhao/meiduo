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

前端：当用户把用户名和密码输入完成之后,会点击登录按钮,这个时候前端应该发送一个axios请求

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

        # 确定使用手机号查询还是用户名查询
        if re.match('1[3-9][0-9]{9}', username):
            User.USERNAME_FIELD = 'mobile'
        else:
            User.USERNAME_FIELD = 'username'

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
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})

        response.set_cookie('username', username)

        return response


"""
前端：
    当用户点击退出按钮的时候，前端发送一个axios delete请求

后端：
    请求
    业务逻辑 退出
    响应 返回JSON数据

"""
from django.contrib.auth import logout


class LogoutView(View):
    def get(self, request):
        # 1. 删除session信息
        logout(request)

        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        # 2. 删除cookie信息,前端根据cookie信息来判断用户是否登录
        response.delete_cookie('username')

        return response


"""
LoginRequiredMixin对于未登录用户会返回重定向,重定向不是JSON数据
"""

from utils.views import LoginRequiredJSONMixin


# 必须是登录用户
class CenterView(LoginRequiredJSONMixin, View):
    def get(self, request):
        # request.user 是已经登录的用户信息
        # request.user 是来源于中间件
        # 系统会进行判断 如果我们确实是登录用户,则可以获取到登录用户对应的模型实例数据
        # 如果我们确实不是登录用户，则request.user = AnonymousUser() 匿名用户
        info_data = {
            'username': request.user.username,
            'email': request.user.email,
            'mobile': request.user.mobile,
            'email_active': request.user.email_active,
        }

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'info_data': info_data})


"""
需求：1.保存邮箱地址  2.发送一封激活邮件  3. 用户激活邮件

前端：
    当用户输入邮箱之后，点击保存。这个时候会发送axios请求。

后端：
    请求 接收请求，获取数据
    业务逻辑 保存邮箱地址  发送一封激活邮件
    响应 JSON  code=0

    路由 PUT     
    步骤
        1. 接收请求
        2. 获取数据
        3. 保存邮箱地址
        4. 发送一封激活邮件
        5. 返回响应

需求(要实现什么功能)-->思路(请求,业务逻辑,响应)-->步骤-->代码实现
"""

"""

1. 设置邮件服务器
    我们设置 163邮箱服务器
    相当于 我们开启了 让163帮助我们发送邮件。同时设置了 一些信息（特别是授权码）
2.  设置邮件发送的配置信息
    #  让django的哪个类来发送邮件
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # 邮件服务器的主机和端口号
    EMAIL_HOST = 'smtp.163.com'
    EMAIL_PORT = 25
    # 使用我的 163服务器 和 授权码
    #发送邮件的邮箱
    EMAIL_HOST_USER = ''
    #在邮箱中设置的客户端授权密码
    EMAIL_HOST_PASSWORD = ''
3. 调用  send_mail 方法
"""

from django.core.mail import send_mail
from apps.users.utils import generic_email_verify_token
from celery_tasks.email.tasks import celery_send_email


class EmailView(LoginRequiredJSONMixin, View):
    def put(self, request):
        # 1. 接收请求
        data = json.loads(request.body.decode())

        # 2. 获取数据
        email = data.get('email')
        # 验证数据
        if re.match('[0-9a-zA-Z_.-]+[@][0-9a-zA-Z_.-]+([.][a-zA-Z]+){1,2}', email):
            pass
        else:
            return JsonResponse({'code': 400, 'errmsg': '邮箱格式错误'})

        # 3. 保存邮箱地址
        # request.user 是已经登录的用户信息
        user = request.user
        user.email = email
        user.save()

        # 4. 发送一封激活邮件

        # subject 主题, message 邮件内容, from_email 发件人, recipient_list 收件人列表
        subject = '美多商城激活邮箱'
        message = ''
        from_email = '美多商城<17858752743@163.com>'
        recipient_list = ['2103098110@qq.com']

        # 4.1 对标签数据进行加密处理
        token = generic_email_verify_token(request.user.id)

        # 4.2 组织激活邮件
        verify_url = "http://www.meiduo.site:8080/success_verify_email.html?token=%s" % token

        html_message = '<p>尊敬的用户您好！</p>' \
                       '<p>感谢您使用美多商城。</p>' \
                       '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                       '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)

        # send_mail(
        #     subject=subject,
        #     message=html_message,
        #     from_email=from_email,
        #     recipient_list=recipient_list,
        # )

        celery_send_email.delay(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
        )

        # 5. 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


"""
需求  激活用户的邮件
前端  用户会点击激活连接,激活连接携带了token
后端：
    请求：接收请求，获取参数，验证参数
    业务逻辑：user_id, 根据用户id查询数据，修改数据
    响应：返回响应JSON
    路由：PUT emails/verification/  说明：token并没有在body里
    步骤：
        1. 接收请求
        2. 获取参数
        3. 验证参数
        4. 获取user_id
        5. 根据用户id查询数据
        6. 修改数据
        7. 返回响应JSON

"""

from apps.users.utils import check_verify_token


class EmailVerifyView(View):
    def put(self, request):
        # 1. 接收请求
        params = request.GET

        # 2. 获取参数
        token = params.get('token')

        # 3. 验证参数
        if token is None:
            return JsonResponse({'code': 400, 'errmsg': '参数缺失'})

        # 4. 获取user_id
        user_id = check_verify_token(token)
        if user_id is None:
            return JsonResponse({'code': 400, 'errmsg': '参数错误'})

        # 5. 根据用户id查询数据
        user = User.objects.get(id=user_id)

        # 6. 修改数据
        user.email_active = True
        user.save()

        # 7. 返回响应JSON
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


from apps.users.models import Address


class AddressCreateView(LoginRequiredJSONMixin, View):

    def post(self, request):
        # 1.接收请求
        data = json.loads(request.body.decode())
        # 2.获取参数，验证参数
        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place')
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        user = request.user
        # 验证参数
        # 2.1 验证必传参数
        if not all([receiver, province_id, city_id, district_id, place, mobile, email]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})
        # 邮箱
        if not re.match('[0-9a-zA-Z_.-]+[@][0-9a-zA-Z_.-]+([.][a-zA-Z]+){1,2}', email):
            return JsonResponse({'code': 400, 'errmsg': '邮箱格式错误'})
        # 手机号
        if not re.match('1[3-9][0-9]{9}', mobile):
            return JsonResponse({'code': 400, 'errmsg': '手机号不满足规则'})

        # 3.数据入库
        address = Address.objects.create(
            user=user,
            title=receiver,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )

        address_dict = {
            'id': address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 4.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'address': address_dict})


class AddressView(LoginRequiredJSONMixin, View):

    def get(self, request):
        # 1.查询指定数据
        user = request.user
        # addresses=user.addresses

        addresses = Address.objects.filter(user=user, is_deleted=False)
        # 2.将对象数据转换为字典数据
        address_list = []
        for address in addresses:
            address_list.append({
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })
        # 3.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'addresses': address_list})


class UpdateDestroyAddressView(View):
    def put(self, request, address_id):
        # 1.接收请求
        data = json.loads(request.body.decode())
        # 2.获取参数，验证参数
        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place')
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        # 验证参数
        # 2.1 验证必传参数
        if not all([receiver, province_id, city_id, district_id, place, mobile, email]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})
        # 邮箱
        if not re.match('[0-9a-zA-Z_.-]+[@][0-9a-zA-Z_.-]+([.][a-zA-Z]+){1,2}', email):
            return JsonResponse({'code': 400, 'errmsg': '邮箱格式错误'})
        # 手机号
        if not re.match('1[3-9][0-9]{9}', mobile):
            return JsonResponse({'code': 400, 'errmsg': '手机号不满足规则'})

        # 更新数据
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email,
            )
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '更新地址失败'})

        address = Address.objects.get(id=address_id)
        address_dict = {
            'id': address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 4.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'address': address_dict})

    def delete(self, request, address_id):
        try:
            address = Address.objects.get(id=address_id)

            address.is_deleted = True
            address.save()
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '删除数据失败'})

        return JsonResponse({'code': 0, 'errmsg': '删除数据失败'})


"""
一 根据页面效果，分析需求
    1. 最近浏览记录只有登录用户才可以访问,只记录登录用户的浏览记录
    2. 浏览记录应该有顺序
    3. 没有分页
二 功能
1.在用户访问商品详情的时候,添加浏览记录
2.在个人中心,展示浏览记录

三 分析
问题1： 保存哪些数据？ 用户id,商品id,顺序(访问时间)
问题2： 保存在哪里？   一般要保存在数据库(缺点:1.慢 2.频繁操作数据库)
                    最好保存在redis中
                    服务器内存比较大:mysql + redis  
user_id,sku_id,顺序

key: value

redis:
    string:   x  
    hash:     x 
    list:     v  
    set:      x  
    zset:     v 
            权重：值
"""

"""
添加浏览记录
    前端：
            当登录用户,访问某一个具体SKU页面的时候,发送一个axios请求,请求携带sku_id
    后端：
         请求：     接收请求，获取请求参数，验证参数
         业务逻辑；  连接redis,先去重,在保存到redsi中,只保存5条记录
         响应：      返回JSON

        路由：     POST   browse_histories 
        步骤：
            1. 接收请求
            2. 获取请求参数
            3. 验证参数
            4. 连接redis list
            5. 去重
            6. 保存到redsi中
            7. 只保存5条记录
            8. 返回JSON
            
展示浏览记录
     前端：
           用户在访问浏览记录的时候,发送axios请求,请求会携带session信息
    后端：
         请求：         
         业务逻辑；    连接redis,获取redis数据（[1,2,3]）.根据商品id进行数据查询，将对象转换为字典
         响应：        JSON

        路由：    GET  
        步骤：
            1. 连接redis
            2. 获取redis数据（[1,2,3]）
            3. 根据商品id进行数据查询
            4. 将对象转换为字典
            5. 返回JSON
"""

from apps.goods.models import SKU
from django_redis import get_redis_connection


class UserHistoryView(LoginRequiredJSONMixin, View):
    def post(self, request):
        user = request.user
        # 1. 接收请求
        data = json.loads(request.body.decode())

        # 2. 获取请求参数
        sku_id = data.get('sku_id')

        # 3. 验证参数
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '没有此商品'})

        # 4. 连接redis list
        redis_cli = get_redis_connection('history')

        # 5. 去重
        redis_cli.lrem('history_%s' % user.id, 0, sku_id)

        # 6. 保存到redsi中
        redis_cli.lpush('history_%s' % user.id, sku_id)

        # 7. 只保存5条记录
        redis_cli.ltrim('history_%s' % user.id, 0, 4)

        # 8. 返回JSON
        return JsonResponse({'code': 0, 'errmsg': 'ok'})

    def get(self, request):
        # 1. 连接redis
        redis_cli = get_redis_connection('history')

        # 2. 获取redis数据（[1,2,3]）
        ids = redis_cli.lrange('history_%s' % request.user.id, 0, 4)

        # 3. 根据商品id进行数据查询
        history_list = []
        for sku_id in ids:
            sku = SKU.objects.get(id=sku_id)
            # 4. 将对象转换为字典
            history_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })

        # 5. 返回JSON
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'skus': history_list})
