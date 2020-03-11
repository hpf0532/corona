import json
import shutil
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.utils.ssh_functions import check_for_controlpersist
import ansible.constants as C
import redis
import datetime
import logging, logging.handlers
from callback_plugins.redis2 import CallbackModule
from tools.config import REDIS_ADDR, REDIS_PORT, REDIS_PD, ansible_result_redis_db
ansible_remote_user = 'root'


class ResultCallback(CallbackBase):
    # Ansible Api 和 Ansible Playbook V2 api 调用该CallBack
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'

    def __init__(self, id):     # 初始化时要求传入任务 id
        super(ResultCallback, self).__init__()
        self.id = id
        self.r = redis.Redis(host=REDIS_ADDR, port=REDIS_PORT, password=REDIS_PD, db=ansible_result_redis_db)

    def _write_to_save(self, data):  # 写入 redis
        msg = json.dumps(data, ensure_ascii=False)
        self.r.rpush(self.id, msg)
        # 为了方便查看，我们 print 写入 redis 的字符串的前 50 个字符
        print("\33[34m写入Redis：%.50s......\33[0m" % msg)

    def v2_playbook_on_play_start(self, play):
        name = play.get_name().strip()
        if not name:
            msg = u"PLAY"
        else:
            msg = u"PLAY [%s]" % name
        print(msg)

    def v2_runner_on_ok(self, result, **kwargs):
        # 处理成功任务，跳过 setup 模块的结果
        host = result._host
        # print("=======================", result._result.keys())
        if "ansible_facts" in result._result.keys():    # 我们忽略 setup 操作的结果
            print("\33[32mSetUp 操作，不Save结果\33[0m")
        else:
            self._write_to_save({
                "host": host.name,
                "result": result._result,
                "task": result.task_name,
                "status": "success"
            })

    def v2_runner_on_failed(self, result, ignore_errors=False, **kwargs):
        # 处理执行失败的任务，有些任务失败会被忽略，所有有两种状态
        host = result._host
        if ignore_errors:
            status = "ignoring"
        else:
            status = 'failed'
        self._write_to_save({
                "host": host.name,
                "result": result._result,
                "task": result.task_name,
                "status": status
            })

    def v2_runner_on_skipped(self, result, *args, **kwargs):
        # 处理跳过的任务
        host = result._host
        self._write_to_save({
                "host": host.name,
                "result": result._result,
                "task": result.task_name,
                "status": "skipped"
            })

    def v2_runner_on_unreachable(self, result, **kwargs):
        # 处理主机不可达的任务
        host = result._host
        self._write_to_save({
                "host": host.name,
                "result": result._result,
                "task": result.task_name,
                "status": "unreachable"
            })

    def v2_playbook_on_notify(self, handler, host):
        pass

    def v2_playbook_on_no_hosts_matched(self):
        pass

    def v2_playbook_on_no_hosts_remaining(self):
        pass

    def v2_playbook_on_start(self, playbook):
        pass


class MyTaskQueueManager(TaskQueueManager):
    def load_callbacks(self):   # 截断callback，只保留 api 自定义
        pass


def ansible_exec_api(tid, hosts, tasks, sources, extra_vars={}):
    Options = namedtuple('Options',
                         ['remote_user',
                          'connection',
                          'module_path',
                          'forks',
                          'become',
                          'become_method',
                          'become_user',
                          'check',
                          'diff'])
    options = Options(remote_user=ansible_remote_user,
                      connection='paramiko',
                      module_path=['/to/mymodules'],
                      forks=10,
                      become=None,
                      become_method=None,
                      become_user=None,
                      check=False,
                      diff=False)
    loader = DataLoader()
    passwords = dict(vault_pass='secret')
    inventory = InventoryManager(loader=loader, sources=sources)
    inventory.add_host("haha")
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    variable_manager.extra_vars=extra_vars
    play_source = dict(name="Ansible Play", hosts=hosts, gather_facts='no', tasks=tasks)
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
    tqm = None
    try:
        tqm = MyTaskQueueManager(
                  inventory=inventory,
                  variable_manager=variable_manager,
                  loader=loader,
                  options=options,
                  passwords=passwords,
                  stdout_callback=ResultCallback(tid),  # 将任务 ID 传递给 ResultCallback
              )
        result = tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()
        shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)


class MyPlaybookExecutor(PlaybookExecutor):
    def __init__(self, tid, playbooks, inventory, variable_manager, loader, options, passwords):
        self._playbooks = playbooks
        self._inventory = inventory
        self._variable_manager = variable_manager
        self._loader = loader
        self._options = options
        self.passwords = passwords
        self._unreachable_hosts = dict()
        if options.listhosts or options.listtasks or options.listtags or options.syntax:
            self._tqm = None
        else:
            self._tqm = MyTaskQueueManager(
                    inventory=inventory,
                    variable_manager=variable_manager,
                    loader=loader,
                    options=options,
                    passwords=self.passwords,
                    stdout_callback=ResultCallback(tid) # 将任务 ID 传递给 ResultCallback
                )
        check_for_controlpersist(C.ANSIBLE_SSH_EXECUTABLE)


def ansible_playbook_api(tid, hosts, playbooks, sources, extra_vars={}):
    Options = namedtuple('Options', [
        'remote_user',
        'connection',
        'module_path',
        'forks',
        'become',
        'become_method',
        'become_user',
        'check',
        'diff',
        'listhosts',
        'listtasks',
        'listtags',
        'syntax',
        ])
    options = Options(
        remote_user=ansible_remote_user,
        connection='paramiko',
        module_path=['/to/mymodules'],
        forks=10,
        become=None,
        become_method=None,
        become_user=None,
        check=False,
        diff=False,
        listhosts=None,
        listtasks=None,
        listtags=None,
        syntax=None
    )
    loader = DataLoader()
    passwords = dict(vault_pass='secret')
    inventory = InventoryManager(loader=loader, sources=sources)
    # 創建默认的主机组
    inventory.add_group("all")
    for host, port in hosts:
        print(host, port)
        inventory.add_host(host, group="all", port=port)

    variable_manager = VariableManager(loader=loader, inventory=inventory)
    variable_manager.extra_vars = extra_vars
    pb = MyPlaybookExecutor(tid=tid,
                            playbooks=playbooks,
                            inventory=inventory,
                            variable_manager=variable_manager,
                            loader=loader,
                            options=options,
                            passwords=passwords)
    # raise ValueError("1123")
    result = pb.run()


if __name__ == '__main__':
    sources = 'scripts/inventory'
    extra_vars = {'content': '这个参数从外部传入'}
    # 测试 ansible_api
    tasks = []
    tasks.append(dict(action=dict(module='debug', args=dict(msg='{{ content }}'))))
    ansible_exec_api(
            "AnsibleApi-%s" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
            "localhost", tasks, sources, extra_vars
        )
    # 测试 ansible-playbook_api
    # extra_vars = {'host': '192.13.2.4'}
    playbooks = ['playbooks/test_debug.yml']
    hosts = [('192.168.1.1', 22), ('tomcat', 22), ('vm1', 22)]

    ansible_playbook_api(
            "AnsiblePlayBookApi-%s" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
            hosts, playbooks, sources, extra_vars
        )
