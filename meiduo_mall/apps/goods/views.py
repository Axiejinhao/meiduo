from django.shortcuts import render

# Create your views here.
# pip install mutagen==1.40
# 上传图片
from fdfs_client.client import Fdfs_client


# 1.创建客户端
# 修改加载配置文件的路径
client = Fdfs_client('utils/fastdfs/client.conf')

# 2.上传图片
# 图片的绝对路径
client.upload_by_filename('/home/xjh/Desktop/img/1.jpg')

# 3.获取file_id,上传成功返回字典数据

