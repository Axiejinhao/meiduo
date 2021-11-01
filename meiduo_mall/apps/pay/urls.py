"""
支付宝为我们测试提供了沙箱(测试)环境


一.设置公钥和私钥

    美多商城一对(我们弄)
    genrsa -out app_private_key.pem 2048
    rsa -in app_private_key.pem -pubout -out app_public_key.pem
    将app_public_key.pem的内容复制到沙箱应用中
    支付宝一对(它自己弄)

在整个支付流程中,我们(美多商城)需要做的就是2件事
1.生成跳转到支付宝的链接
2.保存交易完成后,支付宝返回的交易流水号

"""