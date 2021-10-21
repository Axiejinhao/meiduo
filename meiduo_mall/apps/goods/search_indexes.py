from apps.goods.models import SKU
from haystack import indexes

"""
0. 我们需要在模型所对应的子应用中创建search_indexes.py文件,以方便haystack来检索数据
1. 索引类必须继承自indexes.SearchIndex, indexes.Indexable
2. 必须定义一个字段document=True
    字段名起什么都可以,text只是惯例(大家习惯都这么做)
    所有的索引的这个字段都一致就行
3. use_template=True
    允许我们来单独设置一个文件，来指定哪些字段进行检索
    这个单独的文件创建在
    模板文件夹下/search/indexes/子应用名目录/模型类名小写_text.txt

 数据         <----------Haystack--------->             elasticsearch 

 运作： 我们应该让 haystack 将数据获取到给elasticsearch来生成索引

 在虚拟环境下的终端 python manage.py rebuild_index
"""


class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return SKU

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
