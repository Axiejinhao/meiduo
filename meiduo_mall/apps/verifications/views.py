from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from random import randint
from libs.yuntongxun.sms import CCP

# Create your views here.
"""
前端
    url=http://ip:port/image_codes/uuid/
    
后端
    请求 接受路由的uuid
    业务逻辑 生成图片及其二进制,通过redis把图片验证码保存起来
    响应 返回图片二进制
    路由 GET image_codes/uuid/
"""

from django.views import View


class ImageCodeView(View):
    def get(self, request, uuid):
        # 1.接受路由的uuid
        # 2.生成图片及其二进制
        # text是验证码内容,image是图片二进制
        text, image = captcha.generate_captcha()
        # 3.通过redis把图片验证码保存起来
        redis_cli = get_redis_connection('code')
        # name, time, value
        redis_cli.setex(uuid, 100, text)
        # 4.返回图片二进制
        # content_type: 大类/小类
        return HttpResponse(image, content_type='image/jpeg')


"""
前端
            当用户输入完 手机号，图片验证码之后，前端发送一个axios请求
            sms_codes/18310820644/?image_code=knse&image_code_id=b7ef98bb-161b-437a-9af7-f434bb050643

后端

    请求：     接收请求，获取请求参数（路由有手机号， 用户的图片验证码和UUID在查询字符串中）
    业务逻辑：  验证参数， 验证图片验证码， 生成短信验证码，保存短信验证码，发送短信验证码
    响应：     返回响应
            {‘code’:0,'errmsg':'ok'}


    路由：     GET     sms_codes/18310820644/?image_code=knse&image_code_id=b7ef98bb-161b-437a-9af7-f434bb050643

    步骤：
            1. 获取请求参数
            2. 验证参数
            3. 验证图片验证码
            4. 生成短信验证码
            5. 保存短信验证码
            6. 发送短信验证码
            7. 返回响应
"""


class SmsCodeView(View):
    def get(self, request, mobile):
        # 1.获取请求参数
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 2.验证参数
        if not all([image_code, uuid]):
            return JsonResponse({'code': 400, 'errmag': '参数不全'})

        # 3.验证图片验证码
        redis_cli = get_redis_connection('code')
        redis_image_code = redis_cli.get(uuid)
        if redis_image_code is None:
            return JsonResponse({'code': 400, 'errmag': '图形验证码已过期'})
        if image_code.lower() != redis_image_code.decode().lower():
            return JsonResponse({'code': 400, 'errmag': '图形验证码错误'})

        # 提取发送短信的标记,判断是否发送
        send_flag = redis_cli.get('send_flag_%s' % mobile)
        if send_flag is not None:
            return JsonResponse({'code': 400, 'errmsg': '不要频繁发送短信'})

        # 4.生成短信验证码
        sms_code = '%04d' % randint(0, 9999)

        # 管道
        # A.创建管道
        pipeline = redis_cli.pipeline()

        # B.管道收集命令
        # 5.保存短信验证码
        pipeline.setex(mobile, 300, sms_code)
        # 添加一个发送标记
        pipeline.setex('send_flag_%s' % mobile, 60, 1)
        # C.管道执行命令
        pipeline.execute()

        # 5.保存短信验证码
        # redis_cli.setex(mobile, 300, sms_code)
        # 添加一个发送标记
        # redis_cli.setex('send_flag_%s' % mobile, 60, 1)

        # 6.发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, 1], 1)
        from celery_tasks.sms.tasks import celery_send_sms_code
        # delay的参数等同于任务函数的参数
        celery_send_sms_code.delay(mobile, sms_code)

        # 7.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})
