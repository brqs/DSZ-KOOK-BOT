import json
import yaml
file = open(f"app/config/config.yaml", "r", encoding="utf-8")
acc_data = yaml.load(file, Loader=yaml.Loader)
default_account = acc_data["bf1"]["default_account"]
class record(object):
    # 获取主session
    @staticmethod
    def get_session() -> str:
        """
        获取主session
        :return: session
        """
        file_path = f'./data/battlefield/managerAccount/{default_account}/session.json'
        with open(file_path, 'r', encoding="utf-8") as file_temp2:
            session = json.load(file_temp2)["session"]
            return session

    