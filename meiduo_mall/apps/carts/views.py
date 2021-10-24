from django.shortcuts import render

# Create your views here.
"""
1.  京东的网址 登录用户可以实现购物车，未登录用户可以实现购物车
    淘宝的网址 必须是登录用户才可以实现购物车

2.  登录用户数据保存在服务器里        mysql/redis
                                        mysql
                                        redis  学习， 购物车频繁增删改查
                                        mysql+redis
    未登录用户数据保存在客户端
                                        cookie      

3.  保存哪些数据

    redis:
            user_id,sku_id(商品id),count(数量),selected（选中状态）

    cookie:
            sku_id,count,selected,

4.  数据的组织

    redis:
            user_id,sku_id(商品id),count(数量),selected（选中状态）

            hash
            user_id:
                    sku_id:count
                    xxx_sku_id:selected

            1：  
                    1:10
                    xx_1: True

                    2:20
                    xx_2: False

                    3:30
                    xx_3: True
            13个空间

            优化:
            redis的数据保存在内存中,应该尽量少的占用redis的空间

            user_id:
                    sku_id:count
                    selected:{}

            user_id:
                    1: 10 
                    2: 20
                    3: 30
                    selected_1: {1,3}
            10个空间


            user_id:
                    1: 10 
                    2: -20
                    3: 30
            7个空间

    cookie:
        {
            sku_id: {count:xxx,selected:xxxx},
            sku_id: {count:xxx,selected:xxxx},
            sku_id: {count:xxx,selected:xxxx},
        }


5.
    cookie字典转换为字符串保存起来，数据没有加密

    base64:6个比特位为一个单元

    base64模块使用：
        base64.b64encode()将bytes类型数据进行base64编码，返回编码后的bytes类型数据。
        base64.b64deocde()将base64编码后的bytes类型数据进行解码，返回解码后的bytes类型数据。


    字典 ----> pickle ------二进制------>Base64编码

    pickle模块使用：
        pickle.dumps()将Python数据序列化为bytes类型数据。
        pickle.loads()将bytes类型数据反序列化为python数据。

# 编码数据
# 字典
carts = {
    '1': {'count':10,'selected':True},
    '2': {'count':20,'selected':False},
}


# 字典转换为bytes类型
import pickle
b=pickle.dumps(carts)

# 对bytes类型的数据进行base64编码
import base64
encode=base64.b64encode(b)
# 解码数据

# 将base64编码的数据解码
decode_bytes=base64.b64decode(encode)

# 再对解码的数据转换为字典
pickle.loads(decode_bytes)

6.
请求
业务逻辑（数据的增删改查）
响应


增 （注册）
    1.接收数据
    2.验证数据
    3.数据入库
    4.返回响应

删 
    1.查询到指定记录
    2.删除数据（物理删除，逻辑删除）
    3.返回响应

改  （个人的邮箱）
    1.查询指定的记录
    2.接收数据
    3.验证数据
    4.数据更新
    5.返回响应

查   （个人中心的数据展示，省市区）
    1.查询指定数据
    2.将对象数据转换为字典数据
    3.返回响应

"""

"""
    前端：
        我们点击添加购物车之后，前端将商品id，数量发送给后端

    后端：
        请求：       接收参数，验证参数
        业务逻辑：    根据商品id查询数据库看看商品id对不对
                    数据入库
                    登录用户入redis
                        连接redis
                        获取用户id
                        hash
                        set
                        返回响应
                    未登录用户入cookie
                        先有cookie字典
                        字典转换为bytes
                        bytes类型数据base64编码
                        设置cookie
                        返回响应
        响应：       返回JSON
        路由：       POST  /carts/
        步骤：
                1.接收数据
                2.验证数据
                3.判断用户的登录状态
                4.登录用户保存redis
                    4.1 连接redis
                    4.2 操作hash
                    4.3 操作set
                    4.4 返回响应
                5.未登录用户保存cookie
                    5.1 先有cookie字典
                    5.2 字典转换为bytes
                    5.3 bytes类型数据base64编码
                    5.4 设置cookie
                    5.5 返回响应

"""
import json
from django.views import View
from django.http import JsonResponse
from apps.goods.models import SKU
from django_redis import get_redis_connection
import pickle
import base64


class CartsView(View):
    def post(self, request):
        # 1.接收数据
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')

        # 2.验证数据
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '查无此商品'})

        try:
            count = int(count)
        except Exception:
            count = 1

        # 3.判断用户的登录状态
        # 是否为认证用户is_authenticated
        user = request.user
        if user.is_authenticated:
            # 4.登录用户保存redis
            # 4.1 连接redis
            redis_cli = get_redis_connection('carts')

            # 4.2 操作hash
            # redis_cli = hset(key, field, value)
            redis_cli.hset('carts_%s' % user.id, sku_id, count)

            # 4.3 操作set
            redis_cli.sadd('select_%s' % user.id, sku_id)

            # 4.4 返回响应
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:
            # 5.未登录用户保存cookie
            # 先读取cookie数据
            cookie_carts = request.COOKIES.get('carts')
            if cookie_carts:
                # 数据解密
                carts = pickle.loads(base64.b64decode(cookie_carts))
            else:
                # 5.1 先有cookie字典
                carts = {
                    sku_id: {}
                }
            # 判断新增商品是否在数据库中
            if sku_id in carts:
                # 购物车中已经有该商品id,数量累加
                origin_count = carts[sku_id]['count']
                count += origin_count

            carts[sku_id] = {
                'count': count,
                'selected': True
            }

            # 5.2 字典转换为bytes
            carts_bytes = pickle.dumps(carts)
            # 5.3 bytes类型数据base64编码
            base64encode = base64.b64encode(carts_bytes)

            # 5.4 设置cookie
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            # key, value='', max_age=None
            response.set_cookie('carts', base64encode.decode(), max_age=24 * 3600)

            # 5.5 返回响应
            return response

    """
        1.判断用户是否登录
        2.登录用户查询redis
            2.1 连接redis
            2.2 hash        {sku_id:count}
            2.3 set         {sku_id}
            2.4 遍历判断
            2.5 根据商品商品id查询商品信息
            2.6 将对象数据转换为字典数据
            2.7 返回响应
        3.未登录用户查询cookie
            3.1 读取cookie数据
            3.2 判断是否存在购物车数据
                如果存在，则解码      {sku_id:{count:xxx,selected:xxx}}
                如果不存在，初始化空字典
            3.3 根据商品id查询商品信息
            3.4 将对象数据转换为字典数据
            3.5 返回响应

        合并得:
        
        1.判断用户是否登录
        2.登录用户查询redis
            2.1 连接redis
            2.2 hash        {sku_id:count}
            2.3 set         {sku_id}
            2.4 遍历判断
        3.未登录用户查询cookie
            3.1 读取cookie数据
            3.2 判断是否存在购物车数据
                如果存在，则解码            {sku_id:{count:xxx,selected:xxx}}
                如果不存在，初始化空字典

        4 根据商品id查询商品信息
        5 将对象数据转换为字典数据
        6 返回响应

    """

    def get(self, request):
        # 1.判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 2.登录用户查询redis
            # 2.1 连接redis
            redis_cli = get_redis_connection('carts')

            # 2.2 hash {sku_id:count}集合
            sku_id_counts = redis_cli.hgetall('carts_%s' % user.id)

            # 2.3 set {sku_id}集合
            selected_ids = redis_cli.smembers('selected_%s' % user.id)

            # 2.4 遍历判断
            # 统一数据类型
            carts = {}
            for sku_id, count in sku_id_counts.items():
                carts[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected_ids
                }

        else:
            # 3.未登录用户查询cookie
            # 3.1 读取cookie数据
            cookie_carts = request.COOKIES.get('carts')

            # 3.2 判断是否存在购物车数据
            if cookie_carts is not None:
                # 如果存在，则解码 {sku_id:{count:xxx,selected:xxx}}
                carts = pickle.loads(base64.b64decode(cookie_carts))
            else:
                # 如果不存在，初始化空字典
                carts = {}

        # 4 根据商品id查询商品信息
        # 可以直接遍历carts,也可以获取字典的最外层的key,最外层的所有key就是商品id
        sku_ids = carts.keys()

        # 查询id在sku_ids的数据_
        skus = SKU.objects.filter(id__in=sku_ids)
        sku_list = []

        # 5 将对象数据转换为字典数据
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'price': sku.price,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'selected': carts[sku.id]['selected'],
                'count': int(carts[sku.id]['count']),
                'amount': sku.price * carts[sku.id]['count']
            })

        # 6 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_skus': sku_list})

    """
    1.获取用户信息
    2.接收数据
    3.验证数据
    4.登录用户更新redis
       4.1 连接redis
       4.2 hash
       4.3 set
       4.4 返回响应
    5.未登录用户更新cookie
       5.1 先读取购物车数据
           判断有没有。
           如果有则解密数据
           如果没有则初始化一个空字典
       5.2 更新数据
       5.3 重新最字典进行编码和base64加密
       5.4 设置cookie
       5.5 返回响应
    """

    def put(self, request):
        # 1.获取用户信息
        user = request.user

        # 2.接收数据
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected')

        # 3.验证数据
        if not all([sku_id, count]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '没有此商品'})

        try:
            count = int(count)
        except Exception:
            count = 1

        if user.is_authenticated:

            # 4.登录用户更新redis
            # 4.1 连接redis
            redis_cli = get_redis_connection('carts')

            # 4.2 hash
            redis_cli.hset('carts_%s' % user.id, sku_id, count)

            # 4.3 set
            if selected:
                redis_cli.sadd('selected_%s' % user.id, sku_id)
            else:
                redis_cli.srem('selected_%s' % user.id, sku_id)

            # 4.4 返回响应
            return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_sku': {'count': count, 'selected': selected}})

        else:
            # 5.未登录用户更新cookie
            # 5.1 先读取购物车数据
            cookie_cart = request.COOKIES.get('carts')
            # 判断有没有
            if cookie_cart is not None:
                # 如果有则解密数据
                carts = pickle.loads(base64.b64decode(cookie_cart))
            else:
                # 如果没有则初始化一个空字典
                carts = {}
        # 5.2 更新数据
        if sku_id in carts:
            carts[sku_id] = {
                'count': count,
                'selected': selected
            }

        # 5.3 重新最字典进行编码和base64加密
        new_carts = base64.b64encode(pickle.dumps(carts))

        # 5.4 设置cookie
        response = JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_sku': {'count': count, 'selected': selected}})
        response.set_cookie('carts', new_carts.decode(), max_age=24 * 3600)

        # 5.5 返回响应
        return response

    """
    1.接收请求
    2.验证参数
    3.根据用户状态
    4.登录用户操作redis
        4.1 连接redis
        4.2 hash
        4.3 set
        4.4 返回响应
    5.未登录用户操作cookie
        5.1 读取cookie中的购物车数据
        判断数据是否存在
        存在则解码
        不存在则初始化字典
        5.2 删除数据 {}
        5.3 我们需要对字典数据进行编码和base64的处理
        5.4 设置cookie
        5.5 返回响应
    """

    def delete(self, request):
        # 1.接收请求
        data = json.loads(request.body.decode())

        # 2.验证参数
        sku_id = data.get('sku_id')

        try:
            SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '没有此商品'})

        # 3.根据用户状态
        user = request.user
        if user.is_authenticated:

            # 4.登录用户操作redis
            # 4.1 连接redis
            redis_cli = get_redis_connection('carts')

            # 4.2 hash
            redis_cli.hdel('carts_%s' % user.id, sku_id)

            # 4.3 set
            redis_cli.srem('selected_%s' % user.id, sku_id)

            # 4.4 返回响应
            return JsonResponse({'code': 0, 'errmsg': 'ok'})

        else:
            # 5.未登录用户操作cookie
            # 5.1 读取cookie中的购物车数据
            cookie_cart = request.COOKIES.get('carts')
            # 判断数据是否存在
            if cookie_cart is not None:
                # 存在则解码
                carts = pickle.loads(base64.b64decode(cookie_cart))
            else:
                # 不存在则初始化字典
                carts = {}

            # 5.2 删除数据 {}
            del carts[sku_id]
            # 5.3 我们需要对字典数据进行编码和base64的处理
            new_carts = base64.b64encode(pickle.dumps(carts))

            # 5.4 设置cookie
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('carts', new_carts.decode(), max_age=24 * 3600)

            # 5.5 返回响应
            return response
