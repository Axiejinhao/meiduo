from django.http import HttpResponse
from django.shortcuts import render
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection

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
