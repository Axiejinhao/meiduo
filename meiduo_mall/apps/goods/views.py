from django.shortcuts import render

# # Create your views here.
# # pip install mutagen==1.40
# # 上传图片
# from fdfs_client.client import Fdfs_client
#
#
# # 1.创建客户端
# # 修改加载配置文件的路径
# client = Fdfs_client('utils/fastdfs/client.conf')
#
# # 2.上传图片
# # 图片的绝对路径
# client.upload_by_filename('/home/xjh/Desktop/img/1.jpg')
#
# # 3.获取file_id,上传成功返回字典数据

from django.views import View
from utils.goods import get_categories
from apps.contents.models import ContentCategory


class IndexView(View):
    def get(self, request):
        """
        首页的数据分为2部分
        1部分是 商品分类数据
        2部分是 广告数据
        """

        # 1.商品分类数据
        categories = get_categories()

        # 2.广告数据
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        # 我们把数据传递给模板
        context = {
            'categories': categories,
            'contents': contents,
        }
        return render(request, 'index.html', context)
