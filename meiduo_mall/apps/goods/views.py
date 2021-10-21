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


"""
需求：
        根据点击的分类，来获取分类数据（有排序，有分页）
前端：
        前端会发送一个axios请求， 分类id 在路由中， 
        分页的页码（第几页数据），每页多少条数据，排序也会传递过来
后端：
    请求          接收参数
    业务逻辑       根据需求查询数据，将对象数据转换为字典数据
    响应          JSON

    路由  GET  /list/category_id/skus/
    步骤
        1.接收参数
        2.获取分类id
        3.根据分类id进行分类数据的查询验证
        4.获取面包屑数据
        5.查询分类对应的sku数据，然后排序，然后分页
        6.返回响应
"""

from apps.goods.models import GoodsCategory
from django.http import JsonResponse
from apps.goods.models import SKU
from utils.goods import get_breadcrumb


class ListView(View):
    def get(self, request, category_id):
        # 1.接收参数
        # 排序字段
        ordering = request.GET.get('ordering')
        # 每页数据量
        page_size = request.GET.get('page_size')
        # 第几页数据
        page = request.GET.get('page')

        # 2.获取分类id

        # 3.根据分类id进行分类数据的查询验证
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '参数缺失'})

        # 4.获取面包屑数据
        breadcrumb = get_breadcrumb(category)

        # 5.查询分类对应的sku数据，然后排序，然后分页
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(ordering)
        # 分页
        from django.core.paginator import Paginator
        # object_list, per_page
        # object_list   列表数据
        # per_page      每页多少条数据
        paginator = Paginator(skus, per_page=page_size)

        # 获取指定页码数据
        page_skus = paginator.page(page)

        sku_list = []
        # 将对象转换为字典数据
        for sku in page_skus.object_list:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            })

        # 获取总页数
        total_num = paginator.num_pages

        # 6.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'list': sku_list, 'count': total_num, 'breadcrumb': breadcrumb})


"""
搜索 
1. 不使用like

2. 使用 全文检索即在指定的任意字段中进行检索查询

3. 全文检索方案需要配合搜索引擎来实现

4. 搜索引擎

    原理：  关键词与词条的对应关系，并记录词条的位置

5. Elasticsearch
    进行分词操作 
    分词是指将一句话拆解成多个单字或词，这些字或词便是这句话的关键词

6. 
    数据         <----------Haystack--------->             elasticsearch 
                     ORM(面向对象操作模型)                 mysql,oracle,sqlite,sql server
"""

"""
 我们/数据         <----------Haystack--------->             elasticsearch 

 借助于 haystack 来对接 elasticsearch
 所以 haystack 可以帮助 查询数据
"""

from haystack.views import SearchView
from django.http import JsonResponse


class SKUSearchView(SearchView):
    def create_response(self):
        # 获取搜索的结果
        context = self.get_context()

        sku_list = []
        for sku in context['page'].object_list:
            sku_list.append({
                'id': sku.object.id,
                'name': sku.object.name,
                'price': sku.object.price,
                'default_image_url': sku.object.default_image.url,
                'searchkey': context.get('query'),
                'page_size': context['page'].paginator.num_pages,
                'count': context['page'].paginator.count
            })

        return JsonResponse(sku_list, safe=False)


"""
需求：
    详情页面

    1.分类数据
    2.面包屑
    3.SKU信息
    4.规格信息
    
    详情页面也是需要静态化实现的,
    但是可以先把详情页面的数据展示出来
"""
from utils.goods import get_categories
from utils.goods import get_breadcrumb
from utils.goods import get_goods_specs


class DetailView(View):
    def get(self, request, sku_id):
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            pass
        # 1.分类数据
        categories = get_categories()

        # 2.面包屑
        breadcrumb = get_breadcrumb(sku.category)

        # 3.SKU信息

        # 4.规格信息
        goods_specs = get_goods_specs(sku)
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,
        }
        return render(request, 'detail.html', context)
