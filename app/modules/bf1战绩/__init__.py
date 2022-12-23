import asyncio
import json
import os
import re
import time
import yaml
import uuid
import httpx
import zhconv
import random
import aiohttp
import requests
from PIL import Image, ImageFont, ImageDraw
from bs4 import BeautifulSoup
from loguru import logger
from datetime import date, timedelta
from .record_counter import record


bf_aip_url = 'https://sparta-gw.battlelog.com/jsonrpc/pc/api'
bf_aip_header = {
    "User-Agent": "ProtoHttp 1.3/DS 15.1.2.1.0 (Windows)",
    "X-ClientVersion": "release-bf1-lsu35_26385_ad7bf56a_tunguska_all_prod",
    "X-DbId": "Tunguska.Shipping2PC.Win32",
    "X-CodeCL": "3779779",
    "X-DataCL": "3779779",
    "X-SaveGameVersion": "26",
    "X-HostingGameId": "tunguska",
    "X-Sparta-Info": "tenancyRootEnv = unknown;tenancyBlazeEnv = unknown",
    "Connection": "keep-alive",
}

true = True
false = False
null = ''

access_token = None
access_token_time = None
access_token_expires_time = 0
pid_temp_dict = {
}
file = open(f"app/config/config.yaml", "r", encoding="utf-8")
acc_data = yaml.load(file, Loader=yaml.Loader)
default_account = acc_data["bf1"]["default_account"][0]
limits = httpx.Limits(max_keepalive_connections=None, max_connections=None)
client = httpx.AsyncClient(limits=limits)
if not os.path.exists(f"app/data/battlefield/managerAccount/{default_account}/account.json") or \
        os.path.getsize(f"app/data/battlefield/managerAccount/{default_account}/account.json") == 0:
    logger.error(f"bf1默认查询账号cookie未设置请先检查信息,配置路径:app/data/battlefield/managerAccount/{default_account}/account.json")
    exit()


# 根据玩家名字查找pid
async def getPid_byName(player_name: str) -> dict:
    """
    通过玩家的名字来获得pid
    :param player_name: 玩家姓名
    :return: pid-dict
    """
    global access_token, access_token_time, client, access_token_expires_time
    time_start = time.time()
    if access_token is None or (time.time() - access_token_time) >= int(access_token_expires_time):
        logger.info(f"获取token中")
        # 获取token
        with open(f"app/data/battlefield/managerAccount/{default_account}/account.json", 'r',
                  encoding='utf-8') as file_temp1:
            data_temp = json.load(file_temp1)
            remid = data_temp["remid"]
            sid = data_temp["sid"]
        cookie = f'remid={remid}; sid={sid}'
        url = 'https://accounts.ea.com/connect/auth?response_type=token&locale=zh_CN&client_id=ORIGIN_JS_SDK&redirect_uri=nucleus%3Arest'
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36',
            "Connection": "keep-alive",
            'ContentType': 'application/json',
            'Cookie': cookie
        }
        # async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=header, timeout=5)
        token = eval(response.text)["access_token"]
        access_token = token
        access_token_time = time.time()
        access_token_expires_time = eval(response.text)["expires_in"]
        logger.warning(f"token有效时间:{access_token_expires_time}")
    else:
        token = access_token

    # ea-api获取pid
    url = f"https://gateway.ea.com/proxy/identity/personas?namespaceName=cem_ea_id&displayName={player_name}"
    head = {  # 头部信息
        "Host": "gateway.ea.com",
        "Connection": "keep-alive",
        "Accept": "application/json",
        "X-Expand-Results": "true",
        "Authorization": f"Bearer {token}",
        "Accept-Encoding": "deflate",
    }
    # async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=head, timeout=5)
    response = response.text
    logger.info(f"获取pid耗时:{time.time() - time_start}")
    return eval(response)


# 生成并返回一个uuid
async def get_a_uuid() -> str:
    uuid_result = str(uuid.uuid4())
    return uuid_result


# 获取武器数据
async def get_weapon_data(player_pid: str) -> dict:
    global bf_aip_header, bf_aip_url, client
    session = record.get_session()
    bf_aip_header["X-Gatewaysession"] = session
    body = {
        "jsonrpc": "2.0",
        "method": "Progression.getWeaponsByPersonaId",
        "params": {
            "game": "tunguska",
            "personaId": str(player_pid)
        },
        "id": "79c1df6e-0616-48a9-96b3-71dd3502c6cd"
    }
    # async with httpx.AsyncClient() as client:
    response = await client.post(bf_aip_url, headers=bf_aip_header, data=json.dumps(body), timeout=5)
    response = eval(response.text)
    return response


# 获取载具数据
async def get_vehicle_data(player_pid: str) -> dict:
    global bf_aip_header, bf_aip_url, client
    session = record.get_session()
    bf_aip_header["X-Gatewaysession"] = session
    body = {
        "jsonrpc": "2.0",
        "method": "Progression.getVehiclesByPersonaId",
        "params": {
            "game": "tunguska",
            "personaId": str(player_pid)
        },
        "id": await get_a_uuid()
    }
    # async with httpx.AsyncClient() as client:
    response = await client.post(bf_aip_url, headers=bf_aip_header, data=json.dumps(body), timeout=5)
    response = eval(response.text)
    return response


# 获取玩家战报
async def get_player_stat_data(player_pid: str) -> dict:
    global bf_aip_header, bf_aip_url, client
    session = record.get_session()
    bf_aip_header["X-Gatewaysession"] = session
    body = {
        "jsonrpc": "2.0",
        "method": "Stats.detailedStatsByPersonaId",
        "params": {
            "game": "tunguska",
            "personaId": str(player_pid)
        },
        "id": await get_a_uuid()
    }
    # async with httpx.AsyncClient() as client:
    response = await client.post(bf_aip_url, headers=bf_aip_header, data=json.dumps(body), timeout=5)
    response = eval(response.text)
    return response


# 获取玩家最近游玩服务器
async def get_player_recentServers(player_pid: str) -> dict:
    global bf_aip_header, bf_aip_url, client
    session = record.get_session()
    bf_aip_header["X-Gatewaysession"] = session
    body = {
        "jsonrpc": "2.0",
        "method": "ServerHistory.mostRecentServers",
        "params": {
            "game": "tunguska",
            "personaId": str(player_pid)
        },
        "id": await get_a_uuid()
    }
    # async with httpx.AsyncClient() as client:
    response = await client.post(bf_aip_url, headers=bf_aip_header, data=json.dumps(body), timeout=5)
    response = eval(response.text)
    return response


# 获取玩家正在游玩的服务器
async def server_playing(player_pid: str) -> str:
    global bf_aip_header, bf_aip_url, client
    session = record.get_session()
    bf_aip_header["X-Gatewaysession"] = session
    body = {
        "jsonrpc": "2.0",
        "method": "GameServer.getServersByPersonaIds",
        "params":
            {
                "game": "tunguska",
                # pid数组形式
                "personaIds": [player_pid]
            },
        "id": await get_a_uuid()
    }
    # noinspection PyBroadException
    try:
        # async with httpx.AsyncClient() as client:
        response = await client.post(bf_aip_url, headers=bf_aip_header, data=json.dumps(body), timeout=5)
        response = response.text
        # print(response)
        result = eval(response)["result"]
        if type(result["%s" % player_pid]) == str:
            logger.info("玩家未在线/未进入服务器游玩")
            return "玩家未在线/未进入服务器游玩"
        else:
            return result["%s" % player_pid]
    except Exception as e:
        logger.error(e)
        return "获取失败!"


# 获取皮肤列表
async def FullInventory():
    global bf_aip_header, bf_aip_url, client
    session = record.get_session()
    bf_aip_header["X-Gatewaysession"] = session
    body = {
        "jsonrpc": "2.0",
        "method": "Battlepack.listFullInventory",
        "params": {
            "game": "tunguska",
        },
        "id": await get_a_uuid()
    }
    # async with httpx.AsyncClient() as client:
    response = await client.post(bf_aip_url, headers=bf_aip_header, data=json.dumps(body), timeout=5)
    response = response.text
    return response
async def playerPicDownload(url, name):
    file_name = "app/data/battlefield/pic/avatar" + url[url.rfind('/')] + name + ".jpg"
    # noinspection PyBroadException
    try:
        fp = open(file_name, 'rb')
        fp.close()
        return file_name
    except Exception as e:
        logger.warning(f"未找到玩家{name}头像,开始下载:{e}")
        i = 0
        while i < 3:
            async with aiohttp.ClientSession() as session:
                # noinspection PyBroadException
                try:
                    async with session.get(url, timeout=5, verify_ssl=False) as resp:
                        pic = await resp.read()
                        fp = open(file_name, 'wb')
                        fp.write(pic)
                        fp.close()
                        return file_name
                except Exception as e:
                    logger.error(e)
                    i += 1
        return "app/data/battlefield/pic/avatar/play.jpg"
# 下载武器图片
async def PicDownload(url):
    file_name = "app/data/battlefield/pic/weapons" + url[url.rfind('/'):]
    # noinspection PyBroadException
    try:
        fp = open(file_name, 'rb')
        fp.close()
        return file_name
    except Exception as e:
        logger.warning(e)
        i = 0
        while i < 3:
            async with aiohttp.ClientSession() as session:
                # noinspection PyBroadException
                try:
                    async with session.get(url, timeout=5, verify_ssl=False) as resp:
                        pic = await resp.read()
                        fp = open(file_name, 'wb')
                        fp.write(pic)
                        fp.close()
                        return file_name
                except Exception as e:
                    logger.error(e)
                    i += 1
        return "app/data/battlefield/pic/weapons/play.jpg"
async def player_stat_bfban_api(player_pid) -> dict:
    bfban_url = 'https://api.gametools.network/bfban/checkban?personaids=' + str(player_pid)
    bfban_head = {
        "Connection": "keep-alive",
    }
    # noinspection PyBroadException
    try:
        # async with httpx.AsyncClient() as client:
        response = await client.get(bfban_url, headers=bfban_head, timeout=3)
    except Exception as e:
        logger.error(e)
        return "查询失败"
    bf_html = response.text
    if bf_html == "timed out":
        return "查询失败"
    elif bf_html == {}:
        return "查询失败"
    return eval(bf_html)
async def tyc_waterGod_api(player_pid):
    url1 = 'https://api.s-wg.net/ServersCollection/getPlayerAll?PersonId=' + str(player_pid)
    header = {
        "Connection": "keep-alive"
    }
    # async with httpx.AsyncClient() as client:
    response = await client.get(url1, headers=header, timeout=10)
    return response


async def tyc_record_api(player_pid):
    record_url = "https://record.ainios.com/getReport"
    data = {
        "personaId": player_pid
    }
    header = {
        "Connection": "keep-alive"
    }
    # async with httpx.AsyncClient() as client:
    response = await client.post(record_url, headers=header, data=data, timeout=5)
    return response


async def tyc_bfban_api(player_pid):
    bfban_url = 'https://api.gametools.network/bfban/checkban?personaids=' + str(player_pid)
    header = {
        "Connection": "keep-alive"
    }
    # async with httpx.AsyncClient() as client:
    response = await client.get(bfban_url, headers=header, timeout=3)
    return response


async def tyc_bfeac_api(player_name):
    check_eacInfo_url = f"https://api.bfeac.com/case/EAID/{player_name}"
    header = {
        "Connection": "keep-alive"
    }
    # async with httpx.AsyncClient() as client:
    response = await client.get(check_eacInfo_url, headers=header, timeout=10)
    return response


async def tyc_check_vban(player_pid) -> dict or str:
    url = f"https://api.gametools.network/manager/checkban?playerid={player_pid}&platform=pc&skip_battlelog=false"
    head = {
        'accept': 'application/json',
        "Connection": "Keep-Alive"
    }
    try:
        # async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=head, timeout=5)
        try:
            return eval(response.text)
        except:
            return "获取出错!"
    except:
        return '网络出错!'
# 下载交换皮肤
async def download_skin(url):
    file_name = 'app/data/battlefield/pic/skins/' + url[url.rfind('/') + 1:]
    # noinspection PyBroadException
    try:
        fp = open(file_name, 'rb')
        fp.close()
        return file_name
    except Exception as e:
        logger.warning(e)
        i = 0
        while i < 3:
            async with aiohttp.ClientSession() as session:
                # noinspection PyBroadException
                try:
                    async with session.get(url, timeout=5, verify_ssl=False) as resp:
                        pic = await resp.read()
                        fp = open(file_name, 'wb')
                        fp.write(pic)
                        fp.close()
                        return file_name
                except Exception as e:
                    logger.error(e)
                    i += 1
        return None
widths = [
    (126, 1), (159, 0), (687, 1), (710, 0), (711, 1),
    (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
    (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1),
    (8426, 0), (9000, 1), (9002, 2), (11021, 1), (12350, 2),
    (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1),
    (55203, 2), (63743, 1), (64106, 2), (65039, 1), (65059, 0),
    (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
    (120831, 1), (262141, 2), (1114109, 1),
]
def get_width(o):
    """Return the screen column width for unicode ordinal o."""
    global widths
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1
# 下载百科图片
async def download_baike(url):
    file_name = 'app/data/battlefield/pic/百科/' + url[url.rfind('/') + 1:]
    # noinspection PyBroadException
    try:
        fp = open(file_name, 'rb')
        fp.close()
        return file_name
    except Exception as e:
        logger.warning(e)
        i = 0
        while i < 3:
            async with aiohttp.ClientSession() as session:
                # noinspection PyBroadException
                try:
                    async with session.get(url, timeout=5, verify_ssl=False) as resp:
                        pic = await resp.read()
                        fp = open(file_name, 'wb')
                        fp.write(pic)
                        fp.close()
                        return file_name
                except Exception as e:
                    logger.error(e)
                    i += 1
        return None