REDIS_ADDR = '127.0.0.1'
REDIS_PORT = 6379
REDIS_PD = ''
ansible_result_redis_db  = 10
# 连接远程服务器使用的用户名
#ansible_remote_user = 'shiyanlou'
broker_db = 3
result_db = 4

# 指定服务器与组关系的文件
inventory = 'scripts/inventory'
# broker 地址
BROKER = "redis://:%s@127.0.0.1:6379/%s" % (REDIS_PD, broker_db)
# 结果保存地址
BACKEND = "redis://:%s@127.0.0.1:6379/%s" % (REDIS_PD, result_db)
