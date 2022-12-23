import time
import yaml
from typing import Union


class rsp_log(object):

    @staticmethod
    def init_log():
        with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'r', encoding="utf-8") as file1:
            data = yaml.load(file1, yaml.Loader)
            if data is None:
                data = {
                    "total": [],
                    "operators": {}
                }
                with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'w',
                          encoding="utf-8") as file_temp2:
                    yaml.dump(data, file_temp2, allow_unicode=True)

    @staticmethod
    def kick_logger(kook_id: Union[int, str],action_object: str, server_id, reason: str):
        """
        记录踢人的日志
        :param reason: 踢出理由
        :param kook_id: kook号
        :param action_object: 踢出对象-name
        :param server_id:服务器serverid
        :return: 无
        """
        # 记录数据 这里进行一个初始化检测
        rsp_log.init_log()
        with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'r', encoding="utf-8") as file1:
            data = yaml.load(file1, yaml.Loader)
            if kook_id not in data["operators"]:
                data["operators"][kook_id] = []
            time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
            data["operators"][kook_id].append(f"{time_now}-踢出-踢出原因:{reason}-{action_object}-{server_id}")
            data["total"].append(f"{time_now}-{kook_id}-踢出-踢出原因:{reason}-{action_object}-{server_id}")
            with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'w',
                      encoding="utf-8") as file_temp2:
                yaml.dump(data, file_temp2, allow_unicode=True)
    @staticmethod
    def ban_logger(kook_id: Union[int, str], action_object: str, server_id, reason: str,):
            """
            记录封禁的日志
            :param reason: 封禁理由
            :param kook_id: kook号
            :param action_object: 封禁对象-name
            :param server_id:服务器serverid
            :return: 无
            """
            # 记录数据 这里进行一个初始化检测
            rsp_log.init_log()
            with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'r', encoding="utf-8") as file1:
                data = yaml.load(file1, yaml.Loader)
                if kook_id not in data["operators"]:
                    data["operators"][kook_id] = []
                time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
                data["operators"][kook_id].append(f"{time_now}-封禁-封禁原因:{reason}-{action_object}-{server_id}")
                data["total"].append(f"{time_now}-{kook_id}-封禁-封禁原因:{reason}-{action_object}-{server_id}")
                with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'w',
                        encoding="utf-8") as file_temp2:
                    yaml.dump(data, file_temp2, allow_unicode=True)
    @staticmethod
    def unban_logger(kook_id: Union[int, str], action_object: str, server_id:str):
        """
        记录解封的日志
        :param kook_id: kook号
        :param action_object: 解封对象-name
        :param server_id:服务器serverid
        :return: 无
        """
        # 记录数据 这里进行一个初始化检测
        rsp_log.init_log()
        with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'r', encoding="utf-8") as file1:
            data = yaml.load(file1, yaml.Loader)
            if kook_id not in data["operators"]:
                data["operators"][kook_id] = []
            time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
            data["operators"][kook_id].append(f"{time_now}-解封-{action_object}-{server_id}")
            data["total"].append(f"{time_now}-{kook_id}-解封-{action_object}-{server_id}")
            with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'w',
                      encoding="utf-8") as file_temp2:
                yaml.dump(data, file_temp2, allow_unicode=True) 
    @staticmethod
    def move_logger(kook_id: Union[int, str],action_object: str, server_id):
        """
        记录挪人的日志
        :param kook_id: kook号 
        :param action_object: move对象-name
        :param server_id:服务器serverid
        :return: 无
        """
        # 记录数据 这里进行一个初始化检测
        rsp_log.init_log()
        with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'r', encoding="utf-8") as file1:
            data = yaml.load(file1, yaml.Loader)
            if kook_id not in data["operators"]:
                data["operators"][kook_id] = []
            time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
            data["operators"][kook_id].append(f"{time_now}-换边-{action_object}-{server_id}")
            data["total"].append(f"{time_now}-{kook_id}-换边-{action_object}-{server_id}")
            with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'w',
                      encoding="utf-8") as file_temp2:
                yaml.dump(data, file_temp2, allow_unicode=True)  
    @staticmethod
    def map_logger(kook_id: Union[int, str], map_name: str, server_id):
        """
        记录换图的日志
        :param map_name:
        :param kook_id: kook号 
        :param server_id:服务器serverid
        :return: 无
        """
        # 记录数据 这里进行一个初始化检测
        rsp_log.init_log()
        with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'r', encoding="utf-8") as file1:
            data = yaml.load(file1, yaml.Loader)
            if kook_id not in data["operators"]:
                data["operators"][kook_id] = []
            time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
            data["operators"][kook_id].append(f"{time_now}-换图:{map_name}-{server_id}")
            data["total"].append(f"{time_now}-{kook_id}-换图:{map_name}-{server_id}")
            with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'w',
                      encoding="utf-8") as file_temp2:
                yaml.dump(data, file_temp2, allow_unicode=True)
    @staticmethod
    def addVip_logger(kook_id: Union[int, str], action_object: str, days: str, server_id):
        """
        记录vip的日志
        :param days: 天数
        :param action_object:操作对象
        :param kook_id: kook号
        :param server_id:服务器serverid
        :return: 无
        """
        # 记录数据 这里进行一个初始化检测
        rsp_log.init_log()
        with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'r', encoding="utf-8") as file1:
            data = yaml.load(file1, yaml.Loader)
            if kook_id not in data["operators"]:
                data["operators"][kook_id] = []
            time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
            data["operators"][kook_id].append(f"{time_now}-上v:{days}-{action_object}-{server_id}")
            data["total"].append(f"{time_now}-{kook_id}-上v:{days}-{action_object}-{server_id}")
            with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'w',
                      encoding="utf-8") as file_temp2:
                yaml.dump(data, file_temp2, allow_unicode=True)
    @staticmethod
    def delVip_logger(kook_id: Union[int, str], action_object: str, server_id):
        """
        记录unvip的日志
        :param action_object:操作对象
        :param kook_id: kook号
        :param server_id:服务器serverid
        :return: 无
        """
        # 记录数据 这里进行一个初始化检测
        rsp_log.init_log()
        with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'r', encoding="utf-8") as file1:
            data = yaml.load(file1, yaml.Loader)
            if kook_id not in data["operators"]:
                data["operators"][kook_id] = []
            time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
            data["operators"][kook_id].append(f"{time_now}-下v-{action_object}-{server_id}")
            data["total"].append(f"{time_now}-{kook_id}-下v-{action_object}-{server_id}")
            with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'w',
                      encoding="utf-8") as file_temp2:
                yaml.dump(data, file_temp2, allow_unicode=True)

    @staticmethod
    def checkVip_logger(kook_id: Union[int, str], action_object: str, server_id):
        """
        记录checkVip的日志
        :param action_object:清理个数
        :param kook_id: kook号
        :param server_id:服务器serverid
        :return: 无
        """
        # 记录数据 这里进行一个初始化检测
        rsp_log.init_log()
        with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'r', encoding="utf-8") as file1:
            data = yaml.load(file1, yaml.Loader)
            if kook_id not in data["operators"]:
                data["operators"][kook_id] = []
            time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
            data["operators"][kook_id].append(f"{time_now}-清理v:{action_object}个-{server_id}")
            data["total"].append(f"{time_now}-{kook_id}-清理v:{action_object}个-{server_id}")
            with open(f'app/data/battlefield/binds/bfgroups/ddf/log.yaml', 'w',
                      encoding="utf-8") as file_temp2:
                yaml.dump(data, file_temp2, allow_unicode=True)
