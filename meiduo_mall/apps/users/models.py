from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser


# Create your models here.
# 1.自己定义模型
# class User(models.Model):
#     username = models.CharField(max_length=20, unique=True)
#     password = models.CharField(max_length=20)
#     mobile = models.CharField(max_length=11, unique=True)


# 2.django自带一个用户模型
# 用户模型有密码加密和验证
class User(AbstractUser):
    mobile = models.CharField(max_length=11, unique=True)
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name
