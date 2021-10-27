"""
需求：
        登录的时候，将cookie数据合并到redis中
前端：

后端：
    请求：         在登录的时候，获取cookie数据
    业务逻辑：      合并到redis中
    响应：

抽象的问题具体化（举个例子）

1. 读取cookie数据
2. 初始化一个字典 用于保存 sku_id:count
    初始化一个列表 用于保存选中的商品id
    初始化一个列表 用于保存未选中的商品id
3. 遍历cookie数据
4. 将字典数据，列表数据分别添加到redis中
5. 删除cookie数据

#######################################

 1.当cookie数据和redis数据 有相同的商品id的时候:以cookie为主
 2.当cookie数据有，redis数据没有的:全部以cookie为主
 3.当redis中有的数据，cookie没有:不动

"""

import pickle
import base64

from django_redis import get_redis_connection


def merge_cookie_to_redis(request, response):
    # 1. 读取cookie数据
    cookie_carts = request.COOKIES.get('carts')

    if cookie_carts is not None:
        carts = pickle.loads(base64.b64decode(cookie_carts))

        # 2. 初始化一个字典 用于保存 sku_id:count
        cookie_dict = {}

        # 初始化一个列表 用于保存选中的商品id
        selected_ids = []

        # 初始化一个列表 用于保存未选中的商品id
        unselected_ids = []

        # 3. 遍历cookie数据
        """
        {
            1: {count:666,selected:True},
            2: {count:999,selected:True},
            5: {count:999,selected:False},
        }
        """
        for sku_id, count_selected_dict in carts.items():
            # 字典数据
            cookie_dict[sku_id] = count_selected_dict['count']
            if count_selected_dict['selected']:
                selected_ids.append(sku_id)
            else:
                unselected_ids.append(sku_id)

        user = request.user

        # 4. 将字典数据，列表数据分别添加到redis中
        redis_cli = get_redis_connection('carts')
        pipeline = redis_cli.pipeline()
        pipeline.hmset('carts_%s' % user.id, cookie_dict)

        if len(selected_ids) > 0:
            # *selected_ids 对列表数据进行解包
            pipeline.sadd('selected_%s' % user.id, *selected_ids)

        if len(unselected_ids) > 0:
            pipeline.srem('selected_%s' % user.id, *unselected_ids)

        pipeline.execute()

        # 5. 删除cookie数据
        response.delete_cookie('carts')

    return response
