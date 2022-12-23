import json
import yaml
import os
import time
file = open(f"app/config/config.yaml", "r", encoding="utf-8")
acc_data = yaml.load(file, Loader=yaml.Loader)
default_account = acc_data["bf1"]["default_account"][0]
class record(object):
    # 创建配置文件
    @staticmethod
    def config_bind(kook_id: int):
        """
        检查创建kook号文件夹-record和bind的json文件
        :param kook_id: kook号
        :return: bool
        """
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        # 创建文件夹
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        # 创建查询记录文件
        if not os.path.isfile(file_path + f'/record.json'):
            init_data = {
                "bind": {
                    "history": [

                    ]
                },
                "weapon": {
                    "history": [

                    ]
                },
                "vehicle": {
                    "history": [

                    ]
                },
                "stat": {
                    "history": [

                    ]
                },
                "recent": {
                    "history": [

                    ]
                },
                "matches": {
                    "history": [

                    ]
                },
                "server_playing": {
                    "history": [

                    ]
                },
                "lookup_other": {
                    "history": [
                    ]
                }
            }
            with open(f"{file_path}/record.json", 'w', encoding="utf-8") as file_temp:
                json.dump(init_data, file_temp, indent=4)
        # 创建绑定文件
        if not os.path.exists(file_path + f'/bind.json'):
            open(f"{file_path}/bind.json", 'w', encoding="utf-8")
        return True

    # 检查绑定没有
    @staticmethod
    def check_bind(kook_id: int) -> bool:
        """
        检查绑定没有
        :param kook_id: kook号
        :return: bool
        """
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        # 创建文件夹
        if os.path.exists(file_path):
            return True
        else:
            return False

    # 从绑定的缓存获取pid
    @staticmethod
    def get_bind_pid(kook_id: int) -> int:
        """
        从绑定的缓存获取pid
        :param kook_id: kook号
        :return: pid
        """
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/bind.json", 'r', encoding="utf-8") as file_temp:
            data = json.load(file_temp)
            pid = data['personas']['persona'][0]['personaId']
            return pid

    # 从缓存获取displayname
    @staticmethod
    def get_bind_name(kook_id: int) -> str:
        """
        从绑定的缓存获取pid
        :param kook_id: kook号
        :return: pid
        """
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/bind.json", 'r', encoding="utf-8") as file_temp:
            data = json.load(file_temp)
            name = data['personas']['persona'][0]['displayName']
            return name

    # 从缓存获取uid
    @staticmethod
    def get_bind_uid(kook_id: int) -> str:
        """
        从绑定的缓存获取pid
        :param kook_id: kook号
        :return: pid
        """
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/bind.json", 'r', encoding="utf-8") as file_temp:
            data = json.load(file_temp)
            name = data['personas']['persona'][0]['pidId']
            return name

    # 获取主session
    @staticmethod
    def get_session() -> str:
        """
        获取主session
        :return: session
        """
        file_path = f'app/data/battlefield/managerAccount/{default_account}/session.json'
        with open(file_path, 'r', encoding="utf-8") as file_temp2:
            session = json.load(file_temp2)["session"]
            return session
    # 绑定计数
    @staticmethod
    def bind_counter(kook_id: int, bind_info: str):
        """
        绑定计数器
        :param kook_id: kook号
        :param bind_info: 绑定的name和pid
        :return: None
        """
        time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
        record.config_bind(kook_id)
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            data_temp["bind"]["history"].append(f"{time_now}-{bind_info}")
            with open(f"{file_path}/record.json", 'w', encoding="utf-8") as file_temp2:
                json.dump(data_temp, file_temp2, indent=4, ensure_ascii=False)

    # 获取绑定次数
    @staticmethod
    def get_bind_counter(kook_id: int) -> list:
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            return data_temp["bind"]["history"]

    # 武器计数
    @staticmethod
    def weapon_counter(kook_id: int, player_id: str, player_name: str, weapon_type: str):
        """
        武器计数器
        :param weapon_type: 武器类型
        :param kook_id: kook号
        :param player_id: pid
        :param player_name: 名字
        :return: None
        """
        time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
        record.config_bind(kook_id)
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            data_temp["weapon"]["history"].append(f"{time_now}-{player_id}-{player_name}-{weapon_type}")
            with open(f"{file_path}/record.json", 'w', encoding="utf-8") as file_temp2:
                json.dump(data_temp, file_temp2, indent=4, ensure_ascii=False)

    # 获取武器查询次数
    @staticmethod
    def get_weapon_counter(kook_id: int) -> list:
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            return data_temp["weapon"]["history"]

    # 载具计数
    @staticmethod
    def vehicle_counter(kook_id: int, player_id: str, player_name: str, vehicle_type: str):
        """
        载具
        :param vehicle_type: 载具类型
        :param kook_id: kook号
        :param player_id: pid
        :param player_name: 名字
        :return: None
        """
        time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
        record.config_bind(kook_id)
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            data_temp["vehicle"]["history"].append(f"{time_now}-{player_id}-{player_name}-{vehicle_type}")
            with open(f"{file_path}/record.json", 'w', encoding="utf-8") as file_temp2:
                json.dump(data_temp, file_temp2, indent=4, ensure_ascii=False)

    # 获取载具查询次数
    @staticmethod
    def get_vehicle_counter(kook_id: int) -> list:
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            return data_temp["vehicle"]["history"]

    # 生涯计数
    @staticmethod
    def player_stat_counter(kook_id: int, player_id: str, player_name: str):
        """
        生涯
        :param kook_id: kook号
        :param player_id: pid
        :param player_name: 名字
        :return: None
        """
        time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
        record.config_bind(kook_id)
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            data_temp["stat"]["history"].append(f"{time_now}-{player_id}-{player_name}")
            with open(f"{file_path}/record.json", 'w', encoding="utf-8") as file_temp2:
                json.dump(data_temp, file_temp2, indent=4, ensure_ascii=False)

    # 获取生涯查询次数
    @staticmethod
    def get_stat_counter(kook_id: int) -> list:
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            return data_temp["stat"]["history"]

    # 最近计数
    @staticmethod
    def recent_counter(kook_id: int, player_id: str, player_name: str):
        """
        最近
        :param kook_id: kook号
        :param player_id: pid
        :param player_name: 名字
        :return: None
        """
        time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
        record.config_bind(kook_id)
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            data_temp["recent"]["history"].append(f"{time_now}-{player_id}-{player_name}")
            with open(f"{file_path}/record.json", 'w', encoding="utf-8") as file_temp2:
                json.dump(data_temp, file_temp2, indent=4, ensure_ascii=False)

    # 获取最近查询次数
    @staticmethod
    def get_recent_counter(kook_id: int) -> list:
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            return data_temp["recent"]["history"]

    # 对局计数
    @staticmethod
    def matches_counter(kook_id: int, player_id: str, player_name: str):
        """
        对局
        :param kook_id: kook号
        :param player_id: pid
        :param player_name: 名字
        :return: None
        """
        time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
        record.config_bind(kook_id)
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            data_temp["matches"]["history"].append(f"{time_now}-{player_id}-{player_name}")
            with open(f"{file_path}/record.json", 'w', encoding="utf-8") as file_temp2:
                json.dump(data_temp, file_temp2, indent=4, ensure_ascii=False)

    # 获取对局查询次数
    @staticmethod
    def get_matches_counter(kook_id: int) -> list:
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            return data_temp["matches"]["history"]

    # 天眼查计数
    @staticmethod
    def tyc_counter(kook_id: int, player_id: str, player_name: str):
        """
        天眼查
        :param kook_id: kook号
        :param player_id: pid
        :param player_name: 名字
        :return: None
        """
        time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
        record.config_bind(kook_id)
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            if "tyc" not in data_temp:
                data_temp["tyc"] = {"history": [
                ]}
            data_temp["tyc"]["history"].append(f"{time_now}-{player_id}-{player_name}")
            with open(f"{file_path}/record.json", 'w', encoding="utf-8") as file_temp2:
                json.dump(data_temp, file_temp2, indent=4, ensure_ascii=False)

    # 获取天眼查查询次数
    @staticmethod
    def get_tyc_counter(kook_id: int) -> list:
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            return data_temp["tyc"]["history"]

    # 举报计数
    @staticmethod
    def report_counter(kook_id: int, player_id: str, player_name: str):
        """
        天眼查
        :param kook_id: kook号
        :param player_id: pid
        :param player_name: 名字
        :return: None
        """
        time_now = time.strftime('%Y/%m/%d/%H:%M:%S', time.localtime(time.time()))
        record.config_bind(kook_id)
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            if "report" not in data_temp:
                data_temp["report"] = {"history": [
                ]}
            data_temp["report"]["history"].append(f"{time_now}-举报-{player_id}-{player_name}")
            with open(f"{file_path}/record.json", 'w', encoding="utf-8") as file_temp2:
                json.dump(data_temp, file_temp2, indent=4, ensure_ascii=False)

    # 获取天眼查查询次数
    @staticmethod
    def get_report_counter(kook_id: int) -> list:
        file_path = f'app/data/battlefield/binds/players/{kook_id}'
        with open(f"{file_path}/record.json", 'r', encoding="utf-8") as file_temp:
            data_temp = json.load(file_temp)
            return data_temp["report"]["history"]
    