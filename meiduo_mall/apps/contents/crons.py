"""
将经过数据库查询,已经渲染的HTML页面,写入指定页面
用户可以直接访问已经渲染好的静态页面
在终端的虚拟环境执行 python manage.py crontab add
"""

from apps.contents.models import ContentCategory
from utils.goods import get_categories
import time


def generic_meiduo_index():
    print('----------------%s-----------------' % time.ctime())

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

    # 加载渲染的模板
    from django.template import loader
    index_template = loader.get_template('index.html')

    # 模板渲染
    index_html_data = index_template.render(context)

    # 写入指定文件
    from meiduo_mall import settings
    import os
    file_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'front_end_pc/index.html')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(index_html_data)

