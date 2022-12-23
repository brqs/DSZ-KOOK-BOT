from khl import Bot, Message,MessageTypes
from khl.card import CardMessage, Card, Module, Element, Types, Struct
from loguru import logger
from ...bot import bot
from .api_gateway import *
from .bfgroups_log import *
from .main_session_auto_refresh import *
from ..bf1战绩 import *
import time
from datetime import datetime
import difflib
import io
from ..bf1战绩.info_cache_manager import InfoCache, InfoCache_weapon, InfoCache_vehicle, InfoCache_stat
from ..bf1战绩.choose_bg_pic import bg_pic
from .map_team_info import MapData
from PIL import Image as PIL_Image
from PIL import ImageFont, ImageDraw, ImageFilter, ImageEnhance
file = open(f"app/config/config.yaml", "r", encoding="utf-8")
data = yaml.load(file, Loader=yaml.Loader)
devlist=data["botinfo"]["developer"]
serverdict=data["ddf"]
@bot.command(name="demo")
async def test(msg:Message):
    img_url = await bot.client.create_asset('app/your_path')
    await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
@bot.command(name='hello')
async def world(msg: Message):
    user_list=await msg.ctx.guild.fetch_user_list()
    user_id_list=[user.id for user in user_list]
    logger.info(user_id_list)
    user_id_list_str=" ".join(n for n in user_id_list)
    await msg.reply(user_id_list_str) 
@bot.command(name='test') 
async def test(msg: Message):
    await msg.reply(msg.author_id)
@bot.task.add_interval(hours=12)
async def ten_seconds_interval_tasks():
    await main_session_auto_refresh.auto_refresh_account()
# TODO 1: 搜索服务器
@bot.command(name='searchserver',aliases=["服务器"])
async def search_server(msg: Message, server_name: str="ddf"):
    try:
        result = await api_gateway.search_server_by_name(server_name)
    except Exception as e:
        logger.error(e)
        await msg.reply(f'接口出错，请稍后再试')
        return False
    if result == "timed out":
        await msg.reply(f'网络出错，请稍后再试')
        return False
    if not result:
        await msg.reply(f'共搜索到0个服务器')
        return True
    temp = []
    tempstr=""
    length = len(result)
    if 0 < length <= 3:
        tempstr+=f"共搜到{length}个服务器\n"
        temp.append(f"共搜到{length}个服务器\n")
        tempstr+="=" * 20 + "\n"
        temp.append("=" * 20 + "\n")
        for item in result:
            tempstr+=f'{item["name"]}\n'
            temp.append(f'{item["name"]}\n')
            tempstr+=f'GameId:{item["gameId"]}\n'
            temp.append(f'GameId:{item["gameId"]}\n')
            tempstr+= f'{item["slots"]["Soldier"]["current"]}/{item["slots"]["Soldier"]["max"]}[{item["slots"]["Queue"]["current"]}]({item["slots"]["Spectator"]["current"]}) '
            temp.append(
                f'{item["slots"]["Soldier"]["current"]}/{item["slots"]["Soldier"]["max"]}[{item["slots"]["Queue"]["current"]}]({item["slots"]["Spectator"]["current"]}) ')
            tempstr+=f'{item["mapModePretty"]}-{item["mapNamePretty"]}\n'.replace("流血", "流\u200b血").replace("战争",
                                                                                                               "战\u200b争")
            temp.append(f'{item["mapModePretty"]}-{item["mapNamePretty"]}\n'.replace("流血", "流\u200b血").replace("战争",
                                                                                                               "战\u200b争"))
            if item["description"] != '':
                tempstr+=f'简介:{item["description"]}\n'
                temp.append(f'简介:{item["description"]}\n')
            temp.append("=" * 20 + "\n")
            tempstr+="=" * 20 + "\n"
        temp[-1] = temp[-1].replace("\n", '')
        await msg.reply(tempstr)
        return True
    elif 3 < length <= 10:
        temp.append(f"共搜到{length}个服务器\n")
        temp.append("=" * 20 + "\n")
        for item in result:
            temp.append(f'{item["name"][:30]}\n')
            temp.append(f'GameId:{item["gameId"]}\n')
            temp.append(
                f'{item["slots"]["Soldier"]["current"]}/{item["slots"]["Soldier"]["max"]}[{item["slots"]["Queue"]["current"]}]({item["slots"]["Spectator"]["current"]})  ')
            temp.append(f'{item["mapModePretty"]}-{item["mapNamePretty"]}\n'.replace("流血", "流\u200b血").replace("战争",
                                                                                                               "战\u200b争"))
            temp.append("=" * 20 + "\n")
        temp[-1] = temp[-1].replace("\n", '')
        temp_str = " ".join(n for n in temp)
        await msg.reply(temp_str)    
        return True
    elif length > 10:
        await msg.reply(f"共搜到{length}个服务器,结果过多，请细化搜索词\n")   
# TODO 2: 刷新session
@bot.command(name='xsession')
async def xsession(msg: Message):
    if msg.author_id in devlist[0]:
        await main_session_auto_refresh.auto_refresh_account()
        await msg.reply("刷新成功")
    else:
        await msg.reply("权限不足，请联系开发者获取权限")
# TODO 3: 获取服务器信息
@bot.command(name='get_server_detail',aliases=['sinfo','服务器详情'])
async def get_server_detail(msg: Message,server_gameid: str):
    if server_gameid is None:
        await msg.reply(
            f"请检查输入的服务器gameid"
        )
        return False
    try:
        result = await api_gateway.get_server_fulldetails(server_gameid)
        if result == "":
            raise Exception
    except:
        await msg.reply(
            f'可能网络接口出错/输入gameid有误，请稍后再试'
        )
        return False
    temp = [
        f'{result["serverInfo"]["name"]}\n', "=" * 20 + "\n", f'Gameid:{result["serverInfo"]["gameId"]}\n',
        f'Guid:{result["serverInfo"]["guid"]}\n', f'Serverid:{result["rspInfo"]["server"]["serverId"]}\n',
                                             f"=" * 20 + "\n",
        f'人数:{result["serverInfo"]["slots"]["Soldier"]["current"]}/{result["serverInfo"]["slots"]["Soldier"]["max"]}'
        f'[{result["serverInfo"]["slots"]["Queue"]["current"]}]({result["serverInfo"]["slots"]["Spectator"]["current"]}) ',
        f"收藏:{result['serverInfo']['serverBookmarkCount']}\n",
        f'地图:{result["serverInfo"]["mapModePretty"]}-{result["serverInfo"]["mapNamePretty"]}\n'.replace("流血",
                                                                                                        "流\u200b血").replace(
            "战争", "战\u200b争")
    ]
    try:
        temp.append(f'服主:{result["rspInfo"]["owner"]["displayName"]} Pid:{result["rspInfo"]["owner"]["personaId"]}\n')
    except:
        pass
    if result["serverInfo"]["description"] != '':
        temp.append(f'简介:{result["serverInfo"]["description"]}\n')
    temp.append("=" * 20 + "\n")
    try:
        temp.append(
            f'战队名:{result["platoonInfo"]["name"]}\n战队简写:{result["platoonInfo"]["tag"]} 人数:{result["platoonInfo"]["size"]}\n')
        temp.append(f'战队描述:{result["platoonInfo"]["description"]}\n')
        temp.append("=" * 20 + "\n")
    except:
        pass
    temp.append(
        f'创建时间:{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(result["rspInfo"]["server"]["createdDate"]) / 1000))}\n')
    temp.append(
        f'到期时间:{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(result["rspInfo"]["server"]["expirationDate"]) / 1000))}\n')
    temp.append(
        f'续费时间:{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(result["rspInfo"]["server"]["updatedDate"]) / 1000))}\n')
    temp.append("=" * 20)
    temp_str = " ".join(n for n in temp)
    await msg.reply(temp_str)
# TODO 4: 获取help信息
@bot.command(name='dszhelp',aliases=['帮助','help','h'])
async def dszhlep(msg: Message):
    helpdict={"name": "dsz",
            "version": "0.1",
            "display_name": "kook开黑啦战地一ddf服务器管理机器人",
            "authors": "itsbrqs",
            "description": "用来查询战地一个人战绩、服务器信息的机器人",
            "usage": "帮助菜单\n搜索服务器： 服务器 服务器名 \n 获取服务器详细信息： sinfo gameId \n 刷新管理账号session xsession \n踢 kick k ddf1 xxx\n \
                nk xxx\n \
                ban ddf1 xxx\n  \
                unban ddf1 xxx\n \
                banall bana xxx reason \n \
                unbanall unbana xxx \n \
                move ddf1 xxx 1/2\n \
                map ddf1 要塞 \n \
                vip v ddf1 xxx 3 \n \
                unvip uv ddf1 xxx\n \
                checkvip cv ddf1\n \
                maplist ml ddf1\n \
                viplsit vl ddf1\n \
                banlist bl ddf1\n \
                adminlist al"
            }
    helpstr=""+helpdict["name"] + "是 " + helpdict["display_name"]+",目前版本号为"+helpdict["version"]+",开发者是"+ helpdict["authors"]+"。\n"
    await msg.reply(helpstr)
# TODO 5:  服管功能:  指定服务器序号版 1.踢人 2.封禁/解封 3.换边 4.换图 5.vip
# TODO 5.1: 踢
@bot.command(name='kick',aliases=['踢','k'])
async def kick(msg: Message,server_rank: str, player_name: str, reason: str='kick by dsz ,join kook appeal'):
    # 字数检测
    if len(reason.encode("utf-8"))>30:
        await msg.reply("原因字数过长(汉字10个以内)")
        return False
    # 获取服务器id信息
    if server_rank in serverdict:
        server_id = serverdict[f"{server_rank}"]["sid"][0]
        server_gameid =serverdict[f"{server_rank}"]["gid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False   
    # 查验玩家存不存在
    try:
        player_info = await getPid_byName(player_name)
    except:
        await msg.reply("网络出错，请稍后再试")
        return False
    if player_info['personas'] == {}:
        await msg.reply("玩家[{player_name}]不存在")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']
    # 调用踢人的接口
    star_time = time.time()
    result = await api_gateway.rsp_kickPlayer(server_gameid,player_pid, reason)
    end_time = time.time()
    logger.info(f"踢人耗时:{end_time - star_time}秒")
    if type(result) == str:
        await msg.reply(f"{result}")
        return False
    elif type(result) == dict:
        await msg.reply(f"踢出成功!原因:{reason}")
        rsp_log.kick_logger(msg.author_id,player_name,server_rank,reason)
        return True
    else:
        await msg.reply(f"收到指令:/kick {server_rank} {player_name} {reason}\n但执行出错了")
        return False 
# 不用指定服务器序号
@bot.command(name='kick_no_need_rank',aliases=['踹','nk'])
async def kick_no_need_rank(msg: Message, player_name: str, reason: str='kick by dsz ,join kook appeal'):
    # 字数检测
    if 30 < len(reason.encode("utf-8")):
        await msg.reply("原因字数过长(汉字10个以内)")
        return False
    try:
        player_info = await getPid_byName(player_name)
    except:
        await msg.reply("网络出错，请稍后再试")
        return False
    if player_info['personas'] == {}:
        await msg.reply("玩家[{player_name.result}]不存在")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']
    server_info = await server_playing(player_pid)
    if type(server_info) == str:
        await msg.reply(f"{server_info},如果该玩家在线,请指定服务器序号")
        return False
    else:
        server_gid = server_info["gameId"]
    logger.info(server_gid)
    result = await api_gateway.rsp_kickPlayer(server_gid, player_pid, reason)
    if type(result) == str:
        await msg.reply(f"{result}")
        return False
    elif type(result) == dict:
        await msg.reply(f"踢出成功!原因:{reason}")
        rsp_log.kick_logger(msg.author_id,player_name,server_gid,reason)
        return True
    else:
        await msg.reply(f"收到指令:\\nk {player_name}{reason}\n但执行出错了")
        return False
# 封禁
# TODO 5.2: 封禁,解封
@bot.command(name='add_ban',aliases=['ban'])
async def add_ban(msg: Message,server_rank: str, player_name: str, reason: str='ban by dsz ,join kook appeal'):
    # 字数检测
    if 45 < len(reason.encode("utf-8")):
        await msg.reply("请控制原因在15个汉字以内!")
        return False
    # 获取服务器id信息
    if server_rank in serverdict:
        server_id = serverdict[f"{server_rank}"]["sid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False   
    # 调用ban人的接口
    result = await api_gateway.rsp_addServerBan(server_id,player_name)
    if type(result) == str:
        await msg.reply(f"{result}")
        return False
    elif type(result) == dict:
        await msg.reply(f"封禁成功!原因:{reason}")
        rsp_log.ban_logger(msg.author_id, action_object=player_name, server_id=server_rank,
                           reason=reason)
        return True
    else:
        await msg.reply(
            f"收到指令:\\ban {server_rank} {player_name} {reason}\n但执行出错了")
        return False
# 解封
@bot.command(name='del_ban',aliases=['unban'])
async def del_ban(msg: Message,server_rank: str, player_name: str):
    # 获取服务器id信息
    if server_rank in serverdict:
        server_id = serverdict[f"{server_rank}"]["sid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False
    # 查验玩家存不存在
    try:
        player_info = await getPid_byName(player_name)
    except:
        await msg.reply(f"网络出错，请稍后再试")
        return False
    if player_info['personas'] == {}:
        await msg.reply(f"玩家[{player_name}]不存在")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']   
    # 调用ban人的接口
    result = await api_gateway.rsp_removeServerBan(server_id,player_pid)
    if type(result) == str:
        await msg.reply(f"{result}")
        return False
    elif type(result) == dict:
        await msg.reply(f"解封成功!")
        rsp_log.unban_logger(msg.author_id, action_object=player_name, server_id=server_rank)
        return True
    else:
        await msg.reply(
            f"收到指令:\\unban {server_rank} {player_name} \n但执行出错了")
        return False
# banall
@bot.command(name='add_banall',aliases=['banall', 'bana'])
async def add_banall(msg: Message,player_name: str, reason: str="banall by dsz"):
    # TODO 循环 -> task = ban(id) ->并发 -> 循环 result -> 输出
 # 查验玩家存不存在
    try:
        player_info = await getPid_byName(player_name)
    except:
        await msg.reply(f"网络出错，请稍后再试")
        return False
    if player_info['personas'] == {}:
        await msg.reply(f"玩家[{player_name}]不存在")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']   
    player_name = player_info['personas']['persona'][0]['displayName']
     # 字数检测
    if 45 < len(reason.encode("utf-8")):
        await msg.reply("请控制原因在15个汉字以内!")
        return False
    #session_dict
    j=0
    session_dict={}
    for i in serverdict:
        session_dict[j]={"serverid":serverdict[i]["sid"][0]}
        j+=1
    scrape_index_tasks = [
        asyncio.ensure_future(
            api_gateway.rsp_addServerBan(session_dict[i]["serverid"], player_name)
        )
        for i in session_dict
    ]
    tasks = asyncio.gather(*scrape_index_tasks)
    try:
        await tasks
    except Exception as e:
        await msg.reply(f"执行中出现了一个错误!{e}")
        return False
    banall_result = []
    for i, result in enumerate(scrape_index_tasks):
        result = result.result()
        if type(result) == dict:
            banall_result.append(
                f"{i + 1}服:封禁成功!\n"
            )
            rsp_log.ban_logger(msg.author_id, action_object=player_name,server_id=session_dict[i]["serverid"],reason=reason)
        else:
            banall_result.append(f"{i}服:{result}\n")
    try:
        banall_result[-1] = banall_result[-1].replace("\n", "")
    except:
        pass
    banall_result_str = " ".join(n for n in banall_result)
    await msg.reply(banall_result_str)
# banall
@bot.command(name='del_banall',aliases=['unbanall', 'unbana'])
async def del_banall(msg: Message,player_name: str):
    # TODO 循环 -> task = ban(id) ->并发 -> 循环 result -> 输出
 # 查验玩家存不存在
    try:
        player_info = await getPid_byName(player_name)
    except:
        await msg.reply(f"网络出错，请稍后再试")
        return False
    if player_info['personas'] == {}:
        await msg.reply(f"玩家[{player_name}]不存在")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']   
    player_name = player_info['personas']['persona'][0]['displayName']
    #session_dict
    j=0
    session_dict={}
    for i in serverdict:
        session_dict[j]={"serverid":serverdict[i]["sid"][0]}
        j+=1
    scrape_index_tasks = [
        asyncio.ensure_future(
            api_gateway.rsp_removeServerBan(session_dict[i]["serverid"], player_pid)
        )
        for i in session_dict
    ]
    tasks = asyncio.gather(*scrape_index_tasks)
    try:
        await tasks
    except Exception as e:
        await msg.reply(f"执行中出现了一个错误!{e}")
        return False
    unbanall_result = []
    for i, result in enumerate(scrape_index_tasks):
        result = result.result()
        if type(result) == dict:
            unbanall_result.append(
                f"{i + 1}服:解封成功!\n"
            )
            rsp_log.unban_logger(msg.author_id, action_object=player_name,server_id=session_dict[i]["serverid"])
        else:
            unbanall_result.append(f"{i }服:{result}\n")
    try:
        unbanall_result[-1] = unbanall_result[-1].replace("\n", "")
    except:
        pass
    unbanall_result_str = " ".join(n for n in unbanall_result)
    await msg.reply(unbanall_result_str)
# TODO 5.3: 换边
# 换边
@bot.command(name='move_player',aliases=['move', '换边','挪'])
async def move_player(msg: Message,server_rank: str, player_name: str, team_index: str):
    # 队伍序号检测
    try:
        if int(team_index) not in [0, 1, 2]:
            raise Exception
    except:
        await msg.reply(f"请检查队伍序号(1/2)")
        return False
    else:
        team_index = 0
    # 获取服务器id信息
    if server_rank in serverdict:
        server_id = serverdict[f"{server_rank}"]["sid"][0]
        server_gameid = serverdict[f"{server_rank}"]["gid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False 
    # 查验玩家存不存在
    try:
        player_info = await getPid_byName(player_name)
    except:
        await msg.reply(f"网络出错，请稍后再试")
        return False
    if player_info['personas'] == {}:
        await msg.reply(f"玩家{player_name}不存在")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']
    # 调用挪人的接口
    try:
        result = await api_gateway.rsp_movePlayer(server_gameid, int(player_pid), team_index)
    except:
        await msg.reply(f"网络出错,请稍后再试!")
        return False
    if type(result) == str:
        if "成功" in result:
            await msg.reply(f"更换玩家队伍成功")
            rsp_log.move_logger(msg.author_id,  player_name, server_id)
            return True
        elif "获取玩家列表失败!" == result:
            await msg.reply(f"{result}请指定队伍序号(1/2)")
            return False
        else:
            await msg.reply(result)
            return False
    else:
        await msg.reply(
            f"收到指令:(/move {server_rank} {player_name}\n但执行出错了"
            f"result:{result}")
        return False
# TODO 5.4: 换图
# 换图
@bot.command(name='change_map',aliases=['map', '换图'])
async def change_map(msg:Message,server_rank: str, map_index: str):
     # 获取服务器id信息
    if server_rank in serverdict:
        server_id = serverdict[f"{server_rank}"]["sid"][0]
        server_gameid = serverdict[f"{server_rank}"]["gid"][0]
        server_guid = serverdict[f"{server_rank}"]["guid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False 
    map_list = []
    try:
        map_index = int(map_index)
        if map_index == 2788:
            raise Exception
    except:
        # 识别是否为图池名字
        if map_index == "2788":
            map_index = "阿奇巴巴"
        else:
            map_index = map_index \
                .replace("垃圾厂", "法烏克斯要塞") \
                .replace("2788", "阿奇巴巴").replace("垃圾场", "法烏克斯要塞") \
                .replace("黑湾", "黑爾戈蘭灣").replace("海峡", "海麗絲岬") \
                .replace("噗噗噗山口", "武普库夫山口").replace("绞肉机", "凡爾登高地") \
                .replace("狙利西亞", "加利西亞").replace("沼气池", "法烏克斯要塞") \
                .replace("烧烤摊", "聖康坦的傷痕")
        map_index = zhconv.convert(map_index, 'zh-hk').replace("徵", "征").replace("託", "托")
        # 1.地图池
        result = await api_gateway.get_server_details(server_gameid)
        if type(result) == str:
            await msg.reply(f"获取图池出错!")
            return False
        i = 0
        for item in result["rotation"]:
            map_list.append(f"{item['modePrettyName']}-{item['mapPrettyName']}")
            i += 1
        if map_index != "重開":
            map_index_list = []
            for map_temp in map_list:
                if map_index in map_temp:
                    if map_temp not in map_index_list:
                        map_index_list.append(map_temp)
            if len(map_index_list) == 0:
                map_index_list = list(set(difflib.get_close_matches(map_index, map_list)))
        else:
            map_index_list = [map_list.index(f'{result["mapModePretty"]}-{result["mapNamePretty"]}')]
        if len(map_index_list) > 1:
            i = 0
            choices = []
            for item in map_index_list:
                map_index_list[i] = f"{i}#{item}●\n".replace("流血", "流\u200b血") if (
                        item.startswith('行動模式') and
                        item.endswith(('聖康坦的傷痕', '窩瓦河', '海麗絲岬', '法歐堡', '攻佔托爾', '格拉巴山',
                                       '凡爾登高地', '加利西亞', '蘇瓦松', '流血宴廳', '澤布呂赫',
                                       '索姆河', '武普庫夫山口', '龐然闇影'))) \
                    else f"{i}#{item}\n".replace('流血', '流\u200b血')
                choices.append(str(i))
                i += 1
            map_index_list[-1] = map_index_list[-1].replace("\n", '')
            map_index_list_str=" ".join(n for n in map_index_list)
            await msg.reply(
                f"匹配到多个选项,请输入更加精确的地图名或加上游戏模式名,匹配结果如下:\n {map_index_list_str}", 
            )
            return false
        elif len(map_index_list) == 1:
            if type(map_index_list[0]) != int:
                map_index = map_list.index(map_index_list[0])
            else:
                map_index = map_index_list[0]
        elif len(map_index_list) == 0:
            await msg.reply(f"匹配到0个选项,请输入更加精确的地图名或加上游戏模式名\n匹配名:{map_index}")
            return False
        else:
            await msg.reply(f"这是一个bug(奇怪的bug增加了")
            return False
    # 调用换图的接口
    await msg.reply(f"执行ing")
    result = await api_gateway.rsp_changeMap(server_guid, map_index)
    if type(result) == str:
        await msg.reply(f"{result}")
        return False
    elif type(result) == dict:
        if not map_list:
            await msg.reply(
                f"成功更换服务器{server_rank}地图"
            )
            rsp_log.map_logger(msg.author_id, map_index, server_id)
            return True
        else:
            await msg.reply(
                f"成功更换服务器{server_rank}地图为:{map_list[int(map_index)]}".replace('流血', '流\u200b血').replace('\n', '')
            )
            rsp_log.map_logger(msg.author_id,
                               map_list[int(map_index)][map_list[int(map_index)].find('#') + 1:].replace('-',
                                                                                                         ' ').replace(
                                   '\n', ''), server_id)
            return True
    else:
        await msg.reply(f"收到指令:(\map {server_rank}\n但执行出错了")
        return False  
# 图池序号换图
@bot.command(name='change_map_bylist',aliases=['maplist', '图池'])
async def change_map_bylist(msg: Message,server_rank: str):
# 获取服务器id信息
    if server_rank in serverdict:
        server_gameid = serverdict[f"{server_rank}"]["gid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False 
    # 获取地图池
    result = await api_gateway.get_server_details(server_gameid)
    if type(result) == str:
        await msg.reply(f"获取图池时网络出错!")
        return False
    map_list = []
    choices = []
    i = 0
    for item in result["rotation"]:
        map_list.append(
            f"{i}#{item['modePrettyName']}-{item['mapPrettyName']}●\n".replace('流血', '流\u200b血')
            if (
                    item['modePrettyName'] == '行動模式'
                    and
                    item['mapPrettyName'] in
                    [
                        '聖康坦的傷痕', '窩瓦河',
                        '海麗絲岬', '法歐堡', '攻佔托爾', '格拉巴山',
                        '凡爾登高地', '加利西亞', '蘇瓦松', '流血宴廳', '澤布呂赫',
                        '索姆河', '武普庫夫山口', '龐然闇影'
                    ]
            )
            else f"{i}#{item['modePrettyName']}-{item['mapPrettyName']}\n".replace('流血', '流\u200b血')
        )
        choices.append(str(i))
        i += 1
    map_list_str=" ".join(n for n in map_list)
    await msg.reply(f"获取到图池:\n {map_list_str}")   
# TODO 5.5: vip
def vip_file_bak(old_name):
    old_name = old_name
    index = old_name.rfind('.')
    if index > 0:
        # 提取后缀，这里提取不到，后面拼接新文件名字的时候就会报错
        postfix = old_name[index:]
    else:
        logger.error("备份出错!")
        return
    new_name = old_name[:index] + 'bak' + postfix
    # 备份文件写入数据
    old_f = open(old_name, 'rb')
    con = old_f.read()
    if len(con) == 0:  # 当没有内容备份时终止循环
        new_f = open(new_name, 'rb')
        if len(new_f.read()) != 0:
            old_f = open(old_name, 'wb')
            con = new_f.read()
            old_f.write(con)
            logger.success("已经自动还原失效vip文件!")
            return
        logger.warning("vip文件失效!")
        return
    new_f = open(new_name, 'wb')
    new_f.write(con)
    # 关闭文件
    old_f.close()
    new_f.close()
    logger.success("备份文件成功")
    # 增加天数
async def add_day_vip(time_temp: int, time_before: str):
    """
    :param time_temp: 要增加的天数
    :param time_before: 原来的日期
    :return: 增加后的天数-str:2022-02-26
    """
    time_temp = time_temp * 3600 * 24 + int(time.mktime(time.strptime(time_before, "%Y-%m-%d")))
    time_after = datetime.fromtimestamp(time_temp).strftime("%Y-%m-%d")
    return time_after


# 比较今天和指定日期之间相差的天数
async def get_days_diff(time_temp: str):
    """
    :param time_temp: 指定比较的实际如:2022-5-12
    :return: int
    """
    # 获取今天的时间戳time_tempt
    nowTime_str = datetime.now().strftime('%Y-%m-%d')
    time1 = time.mktime(time.strptime(nowTime_str, '%Y-%m-%d'))
    time2 = time.mktime(time.strptime(time_temp, '%Y-%m-%d'))
    # 日期转化为int比较
    diff = (int(time1) - int(time2)) / 24 / 3600
    # print(diff)
    return diff
# 1.根据guid找到服务器文件夹 2.如果文件夹没有vip.json文件就创建 3.读取fullInfo，从里面读取vip列表
# 4.写入info的信息到json 5.如果vip玩家在名单内就加时间 6.不在就调用接口
@bot.command(name='add_vip',aliases=['vip', 'v'])
async def add_vip(msg:Message,server_rank: str, player_name: str, days: str):
     # 获取服务器id信息
    if server_rank in serverdict:
        server_id = serverdict[f"{server_rank}"]["sid"][0]
        server_gameid = serverdict[f"{server_rank}"]["gid"][0]
        server_guid = serverdict[f"{server_rank}"]["guid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False 
    # 获取服务器信息-fullInfo
    try:
        server_fullInfo = await api_gateway.get_server_fulldetails(server_gameid)
        if server_fullInfo == "":
            raise Exception
    except Exception as e:
        logger.error(e)
        await msg.reply("获取服务器信息出现错误!")
        return False
    # 获取服务器json文件,不存在就创建文件夹
    server_path = f"app/data/battlefield/servers/{server_guid}"
    file_path = f"app/data/battlefield/servers/{server_guid}/vip.json"
    if not os.path.exists(server_path):
        os.makedirs(server_path)
        vip_data = {}
        for item in server_fullInfo["rspInfo"]["vipList"]:
            vip_data[item["personaId"]] = {"displayName": item["displayName"], "days": "0000-00-00"}
        with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file1:
            json.dump(vip_data, file1, indent=4, ensure_ascii=False)
            await msg.reply(
                "初始化服务器文件成功!"
            )
    else:
        if not os.path.exists(file_path):
            vip_data = {}
            for item in server_fullInfo["rspInfo"]["vipList"]:
                vip_data[item["personaId"]] = {"displayName": item["displayName"], "days": "0000-00-00"}
            with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file1:
                json.dump(vip_data, file1, indent=4, ensure_ascii=False)
                await msg.reply(
                    "初始化服务器文件成功!"
                )

    vip_file_bak(file_path)
    vip_pid_list = {}
    for item in server_fullInfo["rspInfo"]["vipList"]:
        vip_pid_list[item["personaId"]] = item["displayName"]
    vip_name_list = {}
    for item in server_fullInfo["rspInfo"]["vipList"]:
        vip_name_list[item["displayName"].upper()] = item["personaId"]
    # 刷新本地文件,如果本地vip不在服务器vip位就删除,在的话就更新名字 如果服务器pid不在本地，就写入
    with open(f"{server_path}/vip.json", 'r', encoding="utf-8") as file1:
        # 服务器vip信息
        data1 = json.load(file1)
        # 刷新本地
        del_list = []
        for key in data1:
            if key not in vip_pid_list:
                del_list.append(key)
            else:
                data1[key]["displayName"] = vip_pid_list[key]
        for key in del_list:
            del data1[key]
        # 写入服务器的
        for pid in vip_pid_list:
            if pid not in data1:
                data1[pid] = {"displayName": vip_pid_list[pid], "days": "0000-00-00"}
        with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file2:
            json.dump(data1, file2, indent=4)

    # 如果为行动模式且人数为0，则添加失败
    if server_fullInfo["serverInfo"]["mapModePretty"] == "行動模式" and \
            server_fullInfo["serverInfo"]["slots"]["Soldier"]["current"] == 0:
        await msg.reply(
            "当前服务器为行动模式且人数为0,操作失败!"
        )
        return False
    if server_fullInfo["serverInfo"]["mapModePretty"] == "行動模式":
        server_mode = "\n(当前服务器为行动模式)"
    else:
        server_mode = ''
    # 如果在vip位就更新json文件,不在就调用接口,如果没有匹配到天数或为0,就改成永久，如果有天数就进行增加
    player_name=player_name.upper()
    if player_name in vip_name_list:
        player_pid = vip_name_list[player_name]
        with open(f"{server_path}/vip.json", 'r', encoding="utf-8") as file1:
            # 服务器vip信息
            data1 = json.load(file1)
            # 如果没有匹配到天数或为0,就改成永久，如果有天数就进行增加
            if (not days) or (days == "0"):
                data1[player_pid]["days"] = "0000-00-00"
                with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file2:
                    json.dump(data1, file2, indent=4)
                    await msg.reply(
                        f"修改成功!到期时间:永久{server_mode}"
                    )
                    rsp_log.addVip_logger(msg.author_id,  player_name, "永久", server_id)
                    return True
            else:
                try:
                    days = int(days)
                except:
                    await msg.reply(
                        "请检查输入的天数"
                    )
                    return False
                # 如果是0000则说明以前是永久
                if data1[player_pid]["days"] == "0000-00-00":
                    try:
                        data1[player_pid]["days"] = await add_day_vip(days,datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d"))
                    except:
                        await msg.reply(
                            f"添加日期出错!"
                        )
                        return False
                    if data1[player_pid]["days"] < datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d"):
                        await msg.reply(
                            f"操作出错!目的日期小于今天日期\n目的日期:{data1[player_pid]['days']}"
                        )
                        return False
                    with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file2:
                        json.dump(data1, file2, indent=4)
                        await msg.reply(
                            f"修改成功!到期时间:{data1[player_pid]['days']}{server_mode}"
                        )
                        rsp_log.addVip_logger(msg.author_id, player_name, f"{days}天", server_id)
                        return True
                else:
                    try:
                        data1[player_pid]["days"] = await add_day_vip(days, data1[player_pid]["days"])
                    except:
                        await msg.reply(
                            f"添加日期出错!"
                        )
                        return False
                    if data1[player_pid]["days"] < datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d"):
                        await msg.reply(
                            f"操作出错!目的日期小于今天日期\n目的日期:{data1[player_pid]['days']}"
                        )
                        return False
                    with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file2:
                        json.dump(data1, file2, indent=4)
                        await msg.reply(
                            f"修改成功!到期时间:{data1[player_pid]['days']}{server_mode}"
                        )
                        rsp_log.addVip_logger(msg.author_id, player_name, f"{days}天", server_id)
                        return True
    # 不在vip位的情况
    else:
        try:
            result = await api_gateway.rsp_addServerVip(server_id, player_name)
            logger.info(vip_name_list)
        except:
            await msg.reply(
                "网络出错!"
            )
            return False
        # 如果类型为
        if result == "玩家已在vip位":
            await msg.reply(
                "操作出错,未成功识别玩家信息!"
            )
            return False
        elif type(result) == str:
            if "已满" in result:
                await msg.reply(
                    f"服务器vip位已满!{result}"
                )
                return
            await msg.reply(
                result
            )
            return False
        # 字典就是成功的情况
        elif type(result) == dict:
            with open(f"{server_path}/vip.json", 'r', encoding="utf-8") as file1:
                # 服务器vip信息
                data1 = json.load(file1)
                i = 1
                while i <= 5:
                    try:
                        player_info = await getPid_byName(player_name)
                        break
                    except:
                        i += 1
                if i > 5:
                    await msg.reply(
                        f"成功添加玩家[{player_name}]vip但写入时间数据时出错!(比较罕见的情况)"
                    )
                    rsp_log.addVip_logger(msg.author_id, player_name, f"时间出错", server_id)
                    return True
                player_pid = player_info['personas']['persona'][0]['personaId']
                data1[player_pid] = {"displayName": player_name, "days": "0000-00-00"}
                # 写入配置
                # 如果没有匹配到天数或为0,就改成永久，如果有天数就进行增加
                if (not days) or (days== "0"):
                    data1[player_pid]["days"] = "0000-00-00"
                    with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file2:
                        json.dump(data1, file2, indent=4)
                        await msg.reply(
                            f"添加成功!到期时间:永久{server_mode}"
                        )
                        rsp_log.addVip_logger(msg.author_id,player_name, "永久", server_id)
                        return True
                else:
                    try:
                        days = int(days)
                    except:
                        await msg.reply(
                            "请检查输入的天数"
                        )
                        return False
                    try:
                        data1[player_pid]["days"] = await add_day_vip(days,datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d"))
                    except Exception as e:
                        logger.error(e)
                        await msg.reply(
                            f"添加日期出错!"
                        )
                        return False
                    if data1[player_pid]["days"] < datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d"):
                        await msg.reply(
                            f"操作出错!目的日期小于今天日期\n目的日期:{data1[player_pid]['days']}"
                        )
                        return False
                    with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file2:
                        json.dump(data1, file2, indent=4)
                        await msg.reply(
                            f"添加成功!到期时间:{data1[player_pid]['days']}{server_mode}"
                        )
                        rsp_log.addVip_logger(msg.author_id, player_name, f"{days}天", server_id)
                        return True
        else:
            await msg.reply(
                f"收到指令:/vip {server_rank} {player_name} {days}\n但执行出错了"
            )
            return False
# 移除vip
@bot.command(name='del_vip',aliases=['unvip', 'uv'])
async def del_vip(msg:Message,server_rank: str, player_name: str):
    # 查验玩家存不存在
    try:
        player_info = await getPid_byName(player_name)
    except:
        await msg.reply(
            f"网络出错，请稍后再试"
        )
        return False
    if player_info['personas'] == {}:
        await msg.reply(
            f"玩家{player_name}不存在"
        )
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']
    # 获取服务器id信息
    if server_rank in serverdict:
        server_id = serverdict[f"{server_rank}"]["sid"][0]
        server_gameid = serverdict[f"{server_rank}"]["gid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False 
    # 获取服务器信息-fullInfo
    try:
        server_fullInfo = await api_gateway.get_server_fulldetails(server_gameid)
        if server_fullInfo == "":
            raise Exception
    except:
        await msg.reply(
            "获取服务器信息出现错误!"
        )
        return False
    # 如果为行动模式且人数为0，则删除失败
    if server_fullInfo["serverInfo"]["mapModePretty"] == "行動模式" and \
            server_fullInfo["serverInfo"]["slots"]["Soldier"][
                "current"] == 0:
        await msg.reply(
            "当前服务器为行动模式且人数为0,操作失败!"
        )
        return False

    # 调用删除vip的接口
    result = await api_gateway.rsp_removeServerVip(server_id, player_pid)
    logger.info(result)
    if type(result) == str:
        await msg.reply(
            f"{result}"
        )
        return False
    elif type(result) == dict:
        await msg.reply(
            f"删除vip成功"
        )
        rsp_log.delVip_logger(msg.author_id, player_name, server_id)
        return True
    else:
        await msg.reply(
            f"收到指令:/unvip {server_rank} {player_name}\n但执行出错了"
        )
        return False
# 清理过期vip
@bot.command(name='del_vip_timedOut',aliases=['checkvip', 'cv'])
async def del_vip_timedOut(msg:Message,server_rank: str):
     # 获取服务器id信息
    if server_rank in serverdict:
        server_id = serverdict[f"{server_rank}"]["sid"][0]
        server_gameid = serverdict[f"{server_rank}"]["gid"][0]
        server_guid=serverdict[f"{server_rank}"]["guid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False 
    # 获取服务器信息-fullInfo
    try:
        server_fullInfo = await api_gateway.get_server_fulldetails(server_gameid)
        if server_fullInfo == "":
            raise Exception
    except:
        await msg.reply(
            "获取服务器信息出现错误!"
        )
        return False

    # 获取服务器json文件,不存在就创建文件夹
    server_path = f"app/data/battlefield/servers/{server_guid}"
    file_path = f"app/data/battlefield/servers/{server_guid}/vip.json"
    if not os.path.exists(server_path):
        os.makedirs(server_path)
        vip_data = {}
        for item in server_fullInfo["rspInfo"]["vipList"]:
            vip_data[item["personaId"]] = {"displayName": item["displayName"], "days": "0000-00-00"}
        with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file1:
            json.dump(vip_data, file1, indent=4, ensure_ascii=False)
            await msg.reply(
                "初始化服务器文件成功!"
            )
    else:
        if not os.path.exists(file_path):
            vip_data = {}
            for item in server_fullInfo["rspInfo"]["vipList"]:
                vip_data[item["personaId"]] = {"displayName": item["displayName"], "days": "0000-00-00"}
            with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file1:
                json.dump(vip_data, file1, indent=4, ensure_ascii=False)
                await msg.reply(
                    "初始化服务器文件成功!"
                )

    vip_pid_list = {}
    for item in server_fullInfo["rspInfo"]["vipList"]:
        vip_pid_list[item["personaId"]] = item["displayName"]
    vip_name_list = {}
    for item in server_fullInfo["rspInfo"]["vipList"]:
        vip_name_list[item["displayName"].upper()] = item["personaId"]
    # 刷新本地文件,如果本地vip不在服务器vip位就删除,在的话就更新名字 如果服务器pid不在本地，就写入
    with open(f"{server_path}/vip.json", 'r', encoding="utf-8") as file1:
        # 服务器vip信息
        data1 = json.load(file1)
        # 刷新本地
        del_list = []
        for key in data1:
            if key not in vip_pid_list:
                del_list.append(key)
            else:
                data1[key]["displayName"] = vip_pid_list[key]
        for key in del_list:
            del data1[key]
        # 写入服务器的
        for pid in vip_pid_list:
            if pid not in data1:
                data1[pid] = {"displayName": vip_pid_list[pid], "days": "0000-00-00"}
        with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file2:
            json.dump(data1, file2, indent=4)

    # 如果为行动模式且人数为0，则删除失败
    if server_fullInfo["serverInfo"]["mapModePretty"] == "行動模式" and \
            server_fullInfo["serverInfo"]["slots"]["Soldier"][
                "current"] == 0:
        await msg.reply(
            "当前服务器为行动模式且人数为0,操作失败!"
        )
        return False

    # 将过期的pid放进列表里面
    del_list = []
    with open(f"{server_path}/vip.json", 'r', encoding="utf-8") as file1:
        data1 = json.load(file1)
        for pid in data1:
            if data1[pid]["days"] != "0000-00-00":
                if await get_days_diff(data1[pid]["days"]) > 0:
                    del_list.append(pid)
    if len(del_list) == 0:
        await msg.reply(
            f"当前没有过期的vip哦"
        )
        return True
    else:
        await msg.reply(
            f"执行ing,预计移除{len(del_list)}个vip"
        )

    # 记录成功的，失败的
    success = 0
    fail = 0
    # 任务列表
    scrape_index_tasks = [asyncio.ensure_future(api_gateway.rsp_removeServerVip(server_id, item)) for item in
                          del_list]
    tasks = asyncio.gather(*scrape_index_tasks)
    await tasks
    result = []
    for i in scrape_index_tasks:
        result.append(i.result())
    i = 0
    for result_temp in result:
        # 先使用移除vip的接口，再处理vip.json文件
        if type(result_temp) == dict:
            with open(f"{server_path}/vip.json", 'r', encoding="utf-8") as file1:
                dict_temp = json.load(file1)
                del dict_temp[del_list[i]]
                with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file2:
                    json.dump(dict_temp, file2, indent=4)
                    success += 1
        else:
            fail += 1
        i += 1
    await msg.reply(
        f"清理完毕!成功:{success}个,失败:{fail}个"
    )
    rsp_log.checkVip_logger(msg.author_id, success, server_id)
    return True
# 查vip列表
@bot.command(name='get_vipList',aliases=['viplist', 'vl'])
async def get_vipList(msg:Message, server_rank: str):
    # 获取服务器id信息
    if server_rank in serverdict:
        server_id = serverdict[f"{server_rank}"]["sid"][0]
        server_gameid = serverdict[f"{server_rank}"]["gid"][0]
        server_guid=serverdict[f"{server_rank}"]["guid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False 

    # 获取服务器信息-fullInfo
    try:
        server_fullInfo = await api_gateway.get_server_fulldetails(server_gameid)
        if server_fullInfo == "":
            raise Exception
    except:
        await msg.reply(
            "获取服务器信息出现错误!"
        )
        return False
    # 获取服务器json文件,不存在就创建文件夹
    server_path = f"app/data/battlefield/servers/{server_guid}"
    file_path = f"app/data/battlefield/servers/{server_guid}/vip.json"
    if not os.path.exists(server_path):
        os.makedirs(server_path)
        vip_data = {}
        for item in server_fullInfo["rspInfo"]["vipList"]:
            vip_data[item["personaId"]] = {"displayName": item["displayName"], "days": "0000-00-00"}
        with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file1:
            json.dump(vip_data, file1, indent=4, ensure_ascii=False)
            await msg.reply(
                "初始化服务器文件成功!"
            )
    else:
        if not os.path.exists(file_path):
            vip_data = {}
            for item in server_fullInfo["rspInfo"]["vipList"]:
                vip_data[item["personaId"]] = {"displayName": item["displayName"], "days": "0000-00-00"}
            with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file1:
                json.dump(vip_data, file1, indent=4, ensure_ascii=False)
                await msg.reply(
                    "初始化服务器文件成功!"
                )

    vip_file_bak(file_path)

    vip_pid_list = {}
    try:
        for item in server_fullInfo["rspInfo"]["vipList"]:
            vip_pid_list[item["personaId"]] = item["displayName"]
    except:
        await msg.reply(
            "接口出错,请稍后再试"
        )
        return
    vip_name_list = {}
    for item in server_fullInfo["rspInfo"]["vipList"]:
        vip_name_list[item["displayName"].upper()] = item["personaId"]
    # 刷新本地文件,如果本地vip不在服务器vip位就删除,在的话就更新名字 如果服务器pid不在本地，就写入
    with open(f"{server_path}/vip.json", 'r', encoding="utf-8") as file1:
        # 服务器vip信息
        data1 = json.load(file1)
        # 刷新本地
        del_list = []
        for key in data1:
            if key not in vip_pid_list:
                del_list.append(key)
            else:
                data1[key]["displayName"] = vip_pid_list[key]
        for key in del_list:
            del data1[key]
        # 写入服务器的
        for pid in vip_pid_list:
            if pid not in data1:
                data1[pid] = {"displayName": vip_pid_list[pid], "days": "0000-00-00"}
        with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file2:
            json.dump(data1, file2, indent=4)
    # 重新读取vip
    vip_list = []
    with open(f"{server_path}/vip.json", 'r', encoding="utf-8") as file1:
        # 服务器vip信息
        data1 = json.load(file1)
        i=1
        for pid in data1:
            if "days" not in data1[pid]:
                data1[pid]['days'] = data1[pid]['day']
                data1[pid].pop("day")
                with open(f"{server_path}/vip.json", 'w', encoding="utf-8") as file2:
                    json.dump(data1, file2, indent=4)
            if data1[pid]['days'] != '0000-00-00':
                if await get_days_diff(data1[pid]["days"]) > 0:
                    day_temp = f"{data1[pid]['days']}(已过期)"
                else:
                    day_temp = f"{data1[pid]['days']}"
            else:
                day_temp = ""
            temp = f"{i}.{data1[pid]['displayName']}{day_temp}\n"
            vip_list.append(temp)
            i+=1
    vip_list = vip_list
    vip_list_str=" ".join(n for n in vip_list)
    await msg.reply(f"服务器{server_rank}共有{i}位VIP：\n "+vip_list_str)
    
# 查ban列表
@bot.command(name='get_banList',aliases=['banlist', 'bl'])
async def get_banList(msg:Message,server_rank: str):
     # 获取服务器id信息
    if server_rank in serverdict:
        server_id = serverdict[f"{server_rank}"]["sid"][0]
        server_gameid = serverdict[f"{server_rank}"]["gid"][0]
        server_guid=serverdict[f"{server_rank}"]["guid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False 

    # 获取服务器信息-fullInfo
    try:
        server_fullInfo = await api_gateway.get_server_fulldetails(server_gameid)
        if server_fullInfo == "":
            raise Exception
    except:
        await msg.reply(
            "获取服务器信息出现错误!"
        )
        return False
    ban_list = []
    i=1
    try:
        for item in server_fullInfo["rspInfo"]["bannedList"]:
            temp = f"{i}.{item['displayName']}\n"
            ban_list.append(temp)
            i+=1
    except:
        await msg.reply(
            "接口出错,请稍后再试"
        )
        return
    ban_list=random.sample(ban_list,20)
    ban_list_str=" ".join(n for n in ban_list )
    await msg.reply(f"服务器{server_rank}共有{i}ban，{int(i/100)}星ban位：随机展示20位战犯\n {ban_list_str}")
# 查管理列表
@bot.command(name='get_adminList',aliases=['adminlist', 'al'])
async def get_adminList(msg:Message, server_rank: str):
    # 获取服务器id信息
    if server_rank in serverdict:
        server_gameid = serverdict[f"{server_rank}"]["gid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False
    # 获取服务器信息-fullInfo
    try:
        server_fullInfo = await api_gateway.get_server_fulldetails(server_gameid)
        if server_fullInfo == "":
            raise Exception
    except:
        await msg.reply(
            "获取服务器信息出现错误!"
        )
        return False
    admin_list = []
    for item in server_fullInfo["rspInfo"]["adminList"]:
        temp = f"{item['displayName']}\n"
        admin_list.append(temp)
    admin_list = sorted(admin_list)
    admin_len = len(admin_list)
    if admin_len>30:
        admin_list = sorted(admin_list[0:30])
    admin_list_str=" ".join(n for n in admin_list )
    await msg.reply(f"服务器{server_rank}共有{admin_len}位管理\n {admin_list_str}")
# 谁在玩功能
@bot.command(name="who_are_playing",aliases=["谁在玩","谁在捞"])
async def who_are_playing(msg:Message, server_rank: str='ddf1'):
    content=msg.content
    # 获取服务器id信息
    if server_rank in serverdict:
        server_gameid = serverdict[f"{server_rank}"]["gid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False
    # 获取绑定的成员列表
    user_list=await msg.ctx.guild.fetch_user_list()
    user_id_list=[user.id for user in user_list]
    logger.info(user_id_list)
    try:
        group_member_list = []
        bind_path = "app/data/battlefield/binds/players"
        for item in user_id_list:
            group_member_list.append(item)
            if os.path.exists(f"{bind_path}/{item}"):
                try:
                    with open(f"{bind_path}/{item}/bind.json", 'r', encoding="utf-8") as file1:
                        data = json.load(file1)
                        group_member_list.append(data["personas"]["persona"][0]["displayName"].upper())
                except Exception as e:
                    logger.info(e)
        start_time = time.time()
    except Exception as e:
        
        logger.info( e)
    # 获取服务器信息-fullInfo
    try:
        server_fullInfo = await api_gateway.get_server_fulldetails(server_gameid)
        if server_fullInfo == "":
            raise Exception
    except:
        await msg.reply(
            "获取服务器信息出现错误!"
        )
        return False
    admin_list = []
    vip_list = []
    try:
        for item in server_fullInfo["rspInfo"]["adminList"]:
            admin_list.append(f"{item['displayName']}".upper())
        for item in server_fullInfo["rspInfo"]["vipList"]:
            vip_list.append(f"{item['displayName']}".upper())
    except:
        pass

    # gt接口获取玩家列表
    url = "https://api.gametools.network/bf1/players/?gameid=" + str(server_gameid)
    try:
        # async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=5)
    except:
        await msg.reply(
            "网络出错，请稍后再试!"
        )
        return False
    end_time = time.time()
    logger.info(f"获取玩家列表和服务器信息耗时:{end_time - start_time}秒")
    html = response.text
    # 处理网页超时
    if html == "timed out":
        await msg.reply(
            'timed out'
        )
    elif html == {}:
        await msg.reply(
            'timed out'
        )
    elif html == 404:
        await msg.reply(
            "未找到服务器或接口出错"
        )
    html = eval(html)
    if "errors" in html:
        await msg.reply(
            "接口出错，请稍后再试!"
        )
        return False
    try:
        update_time = time.strftime('更新时间:%Y-%m-%d %H:%M:%S', time.localtime(int(html["update_timestamp"])))
    except:
        await msg.reply(
            "接口出错，请稍后再试!"
        )
        return False
    # 统计队伍人数
    try:
        team1_num = len(html["teams"][0]["players"])
        team2_num = len(html["teams"][1]["players"])
    except:
        await msg.reply(
            "获取服务器信息出错,请稍后再试!"
        )
        return False
    # 用来装服务器玩家
    player_list1 = {}
    player_list2 = {}
    i = 0
    while i < team1_num:
        player_list1[f'[{html["teams"][0]["players"][i]["rank"]}]{html["teams"][0]["players"][i]["name"]}'] = "%s" % \
                                                                                                              html[
                                                                                                                  "teams"][
                                                                                                                  0][
                                                                                                                  "players"][
                                                                                                                  i][
                                                                                                                  "join_time"]
        i += 1
    i = 0
    while i < team2_num:
        player_list2[f'[{html["teams"][1]["players"][i]["rank"]}]{html["teams"][1]["players"][i]["name"]}'] = "%s" % \
                                                                                                              html[
                                                                                                                  "teams"][
                                                                                                                  1][
                                                                                                                  "players"][
                                                                                                                  i][
                                                                                                                  "join_time"]
        i += 1
    player_dict_all = player_list1.copy()
    player_dict_all.update(player_list2)
    # 按照加入时间排序
    player_list_all = sorted(player_dict_all.items(), key=lambda kv: ([kv[1]], kv[0]))
    # print(player_list_all[0:20])
    player_list = []
    for item in player_list_all:
        player_list.append(item[0])
    if len(player_list) == 0:
        await msg.reply(
            f"获取到服务器内玩家数为0"
        )
        return
    # 过滤人员
    player_list_filter = []
    for item in group_member_list:
        for i in player_list:
            if i[i.rfind("]") + 1:].upper() in item.upper():
                player_list_filter.append(i + "\n")
    player_list_filter = list(set(player_list_filter))
    i = 0
    for player in player_list_filter:
        if player[player.rfind("]") + 1:].upper().replace("\n", '') in admin_list:
            player_list_filter[i] = f"{player}".replace("\n", "(管理员)\n")
            i += 1
            continue
        elif player[player.rfind("]") + 1:].upper().replace("\n", '') in vip_list:
            player_list_filter[i] = f"{player}".replace("\n", "(vip)\n")
        i += 1
    player_num = len(player_list_filter)
    player_list_filter_str="".join(n for n in player_list_filter)
    logger.info(player_num)
    if player_num != 0:
        player_list_filter[-1] = player_list_filter[-1].replace("\n", '')
        await msg.reply(
            f"服内群友数:{player_num}\n" if "捞" not in content else f"服内捞b数:{player_num}\n"+ player_list_filter_str+
            f"\n{update_time}"
        )
    else:
        await msg.reply(
            f"服内群友数:0"+f"\n{update_time}"
        ) 

# 通过接口获取玩家列表
async def get_playerList_byGameid(server_gameid: Union[str, int, list]) -> Union[str, dict]:
    """
    :param server_gameid: 服务器gameid
    :return: 成功返回字典,失败返回信息
    """
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36',
        'ContentType': 'json',
    }
    api_url = "https://delivery.easb.cc/games/get_server_status"
    if type(server_gameid) != list:
        data = {
            "gameIds": [
                server_gameid
            ]
        }
    else:
        data = {
            "gameIds": server_gameid
        }
    try:
        # async with httpx.AsyncClient() as client:
        response = await client.post(api_url, headers=header, data=json.dumps(data), timeout=5)
        response = eval(response.text)
    except:
        return "网络超时!"
    if type(server_gameid) != list:
        if str(server_gameid) in response["data"]:
            return response["data"][str(server_gameid)]
        else:
            return "获取服务器信息失败!"
    else:
        return response["data"]
async def download_serverMap_pic(url: str) -> str:
    file_name = 'app/data/battlefield/pic/map/' + url[url.rfind('/') + 1:]
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


async def get_server_map_pic(map_name: str) -> str:
    file_path = f"app/data/battlefield/游戏模式/data.json"
    with open(file_path, 'r', encoding="utf-8") as file1:
        data = json.load(file1)["result"]["maps"]
    for item in data:
        if item["assetName"] == map_name:
            try:
                pic = await download_serverMap_pic(item["images"]["JpgAny"].replace("[BB_PREFIX]",
                                                                                    "https://eaassets-a.akamaihd.net/battlelog/battlebinary"))
                return pic
            except:
                return None


def get_team_pic(team_name: str) -> str:
    team_pic_list = os.listdir(f"app/data/battlefield/pic/team/")
    for item in team_pic_list:
        if team_name in item:
            return f"app/data/battlefield/pic/team/{item}"


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


# 图片版玩家列表
@bot.command(name="pl")
async def get_server_playerList_pic(msg:Message,server_rank: str='ddf1'):
    # 获取服务器id信息
    if server_rank in serverdict:
        server_gameid = serverdict[f"{server_rank}"]["gid"][0]
    else:
        logger.error("服务器不存在")
        await msg.reply("服务器不存在")
        return False 

    await msg.reply(
        f"查询ing"

    )
    time_start = time.time()
    try:
        server_info = await api_gateway.get_server_fulldetails(server_gameid)
        if server_info == '':
            raise Exception
    except:
        await msg.reply(
           '响应超时')
        return False
    admin_pid_list = []
    admin_counter = 0
    admin_color = (117, 213, 87)
    for item in server_info["rspInfo"]["adminList"]:
        admin_pid_list.append(str(item['personaId']))
    vip_pid_list = []
    vip_counter = 0
    vip_color = (227, 23, 13)
    for item in server_info["rspInfo"]["vipList"]:
        vip_pid_list.append(str(item['personaId']))
     # 获取绑定的成员列表
    user_list=await msg.ctx.guild.fetch_user_list()
    user_id_list=[user.id for user in user_list]
    try:
        bind_pid_list = []
        bind_path = "app/data/battlefield/binds/players"
        for item in user_id_list:
            bind_pid_list.append(item)
            if os.path.exists(f"{bind_path}/{item}"):
                try:
                    with open(f"{bind_path}/{item}/bind.json", 'r', encoding="utf-8") as file1:
                        data = json.load(file1)
                        bind_pid_list.append(data["personas"]["persona"][0]["displayName"].upper())
                except Exception as e:
                    logger.info(e)
    except Exception as e:
        logger.info( e)
    bind_color = (65, 105, 225)
    bind_counter = 0
    max_level_counter = 0

    # gt接口获取玩家列表
    url = "https://api.gametools.network/bf1/players/?gameid=" + str(server_gameid)
    try:
        # async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=5)
    except:
        await msg.reply(
            "网络出错，请稍后再试!"
        )
        return False
    response_data = eval(response.text)
    if "errors" in response_data:
        await msg.reply(
            "接口出错，请稍后再试!"
        )
        return False
    # 获取时间
    try:
        update_time = time.strftime('更新时间:%Y-%m-%d %H:%M:%S', time.localtime(int(response_data["update_timestamp"])))
    except:
        await msg.reply(
            "接口出错，请稍后再试!"
        )
        return False

    t1_temp = [player_item['player_id'] for player_item in response_data["teams"][0]["players"]]
    t2_temp = [player_item['player_id'] for player_item in response_data["teams"][1]["players"]]
    if (len(t1_temp) + len(t2_temp)) == 0:
        await msg.reply(
            f"服务器内无玩家!\n{update_time}"
        )
        return
    try:
        # 获取玩家生涯战绩
        # 队伍1
        scrape_index_tasks_t1 = [asyncio.ensure_future(InfoCache_stat(str(player_item['player_id'])).get_data()) for
                                player_item in response_data["teams"][0]["players"]]
        tasks = asyncio.gather(*scrape_index_tasks_t1)
        try:
            await tasks
        except:
            pass

        # 队伍2
        scrape_index_tasks_t2 = [asyncio.ensure_future(InfoCache_stat(str(player_item['player_id'])).get_data()) for
                                player_item in response_data["teams"][1]["players"]]
        tasks = asyncio.gather(*scrape_index_tasks_t2)
        try:
            await tasks
        except:
            pass

        # 服务器名
        server_name = response_data["serverinfo"]["name"]
        # MP_xxx
        server_mapName = response_data["serverinfo"]["level"]

        team1_name = MapData.Map_Team_dict[response_data["serverinfo"]["level"]]["Team1"]
        team1_pic = get_team_pic(team1_name)
        team1_pic = PIL_Image.open(team1_pic).convert('RGBA')
        team1_pic = team1_pic.resize((40, 40), PIL_Image.ANTIALIAS)
        team2_name = MapData.Map_Team_dict[response_data["serverinfo"]["level"]]["Team2"]
        team2_pic = get_team_pic(team2_name)
        team2_pic = PIL_Image.open(team2_pic).convert('RGBA')
        team2_pic = team2_pic.resize((40, 40), PIL_Image.ANTIALIAS)

        # 地图路径
        server_map_pic = await get_server_map_pic(server_mapName)
        # 地图作为画布底图并且高斯模糊化
        if server_map_pic is None:
            await msg.reply(
                "网络出错，请稍后再试!"
            )
            return False
        IMG = PIL_Image.open(server_map_pic)
        # 高斯模糊
        IMG = IMG.filter(ImageFilter.GaussianBlur(radius=12))
        # 调低亮度
        IMG = ImageEnhance.Brightness(IMG).enhance(0.7)
        # 裁剪至1920x1080
        box = (0, 70, 1920, 1150)  # 将要裁剪的图片块距原图左边界距左边距离，上边界距上边距离，右边界距左边距离，下边界距上边的距离。
        IMG = IMG.crop(box)

        # 延迟 5:小于50 4:50< <100 3: 150< < 100 2: 150<  <200 1: 250< <300 0:300+
        Ping1 = PIL_Image.open(f"app/data/battlefield/pic/ping/4.png").convert('RGBA')
        Ping1 = Ping1.resize((int(Ping1.size[0] * 0.04), int(Ping1.size[1] * 0.04)), PIL_Image.ANTIALIAS)
        Ping2 = PIL_Image.open(f"app/data/battlefield/pic/ping/3.png").convert('RGBA')
        Ping2 = Ping2.resize((int(Ping2.size[0] * 0.04), int(Ping2.size[1] * 0.04)), PIL_Image.ANTIALIAS)
        Ping3 = PIL_Image.open(f"app/data/battlefield/pic/ping/2.png").convert('RGBA')
        Ping3 = Ping3.resize((int(Ping3.size[0] * 0.04), int(Ping3.size[1] * 0.04)), PIL_Image.ANTIALIAS)
        Ping4 = PIL_Image.open(f"app/data/battlefield/pic/ping/1.png").convert('RGBA')
        Ping4 = Ping4.resize((int(Ping4.size[0] * 0.04), int(Ping4.size[1] * 0.04)), PIL_Image.ANTIALIAS)
        Ping5 = PIL_Image.open(f"app/data/battlefield/pic/ping/0.png").convert('RGBA')
        Ping5 = Ping5.resize((int(Ping5.size[0] * 0.04), int(Ping5.size[1] * 0.04)), PIL_Image.ANTIALIAS)

        draw = ImageDraw.Draw(IMG)
        # 字体路径
        font_path = 'app/data/battlefield/font/BFText-Regular-SC-19cf572c.ttf'
        title_font = ImageFont.truetype(font_path, 40)
        team_font = ImageFont.truetype(font_path, 25)
        title_font_small = ImageFont.truetype(font_path, 22)
        player_font = ImageFont.truetype(font_path, 18)
        rank_font = ImageFont.truetype(font_path, 15)
        info_font = ImageFont.truetype(font_path, 22)
        # 服务器名字
        draw.text((97, 30), f"服务器名:{server_name}", fill='white', font=title_font)
        # 更新时间
        draw.text((100, 80), update_time, fill="white", font=rank_font)
        max_level_color = (255, 132, 0)

        KD_counter1 = 0
        KPM_counter1 = 0
        RANK_counter1 = 0
        TIME_counter1 = 0
        WIN_counter1 = 0
        # 队伍1
        # 队伍1图片
        IMG.paste(team1_pic, (100, 101))
        # 队伍1名
        draw.text((152, 105), team1_name, fill='white', font=team_font)
        draw.text((520, 113), f"胜率", fill='white', font=title_font_small)
        draw.text((610, 113), f"K/D", fill='white', font=title_font_small)
        draw.text((700, 113), f"KPM", fill='white', font=title_font_small)
        draw.text((790, 113), f"时长(h)", fill='white', font=title_font_small)
        draw.text((890, 113), f"延迟", fill='white', font=title_font_small)
        # 队伍1横线
        draw.line([100, 141, 950, 141], fill=(114, 114, 114), width=2, joint=None)
        # 队伍1竖线
        draw.line([100, 155, 100, 915], fill=(114, 114, 114), width=2, joint=None)
        leve_position_1 = None
        for i, player_item in enumerate(response_data["teams"][0]["players"]):
            # 序号
            draw.text((135, 156 + i * 23), f"{i + 1}", anchor="ra", fill='white', font=player_font)

            # 等级框 30*15  等级 居中显示
            draw.rectangle([155, 159 + i * 23, 185, 173.5 + i * 23],
                        fill=max_level_color if player_item['rank'] == 150 else None, outline=None, width=1)
            RANK_counter1 += player_item['rank']
            if player_item['rank'] == 150:
                max_level_counter += 1
            rank_font_temp = ImageFont.truetype(font_path, 15)
            ascent, descent = rank_font_temp.getsize(f"{player_item['rank']}")
            leve_position_1 = 170 - ascent / 2, 165.5 + i * 23 - descent / 2
            draw.text(leve_position_1, f"{player_item['rank']}",
                    fill="white",
                    font=rank_font)
            # 战队 名字
            color_temp = 'white'
            if str(player_item["name"]).upper() in bind_pid_list:
                color_temp = bind_color
                bind_counter += 1
            if str(player_item["player_id"]) in vip_pid_list:
                color_temp = vip_color
                vip_counter += 1
            if str(player_item["player_id"]) in admin_pid_list:
                color_temp = admin_color
                admin_counter += 1
            if player_item["platoon"] != "":
                draw.text((195, 155 + i * 23), f"[{player_item['platoon']}]{player_item['name']}", fill=color_temp,
                        font=player_font)
            else:
                draw.text((195, 155 + i * 23), player_item["name"], fill=color_temp, font=player_font)

            # 延迟 靠右显示
            ping_pic = Ping5
            if player_item['latency'] <= 50:
                ping_pic = Ping1
            elif 50 < player_item['latency'] <= 100:
                ping_pic = Ping2
            elif 100 < player_item['latency'] <= 150:
                ping_pic = Ping3
            elif 150 < player_item['latency']:
                ping_pic = Ping4
            IMG.paste(ping_pic, (880, 158 + i * 23), ping_pic)
            draw.text((930, 155 + i * 23), f"{player_item['latency']}", anchor="ra", fill='white', font=player_font)

            # KD KPM 时长
            try:
                player_stat_data = scrape_index_tasks_t1[i].result()["result"]
                # 胜率
                win_p = int(player_stat_data['basicStats']['wins'] / (
                        player_stat_data['basicStats']['losses'] + player_stat_data['basicStats']['wins']) * 100)
                WIN_counter1 += win_p
                draw.text((565, 155 + i * 23), f'{win_p}%', anchor="ra", fill=max_level_color if win_p >= 70 else 'white',
                        font=player_font)
                # kd
                kd = player_stat_data['kdr']
                KD_counter1 += kd
                draw.text((645, 155 + i * 23), f'{kd}', anchor="ra", fill=max_level_color if kd >= 3 else 'white',
                        font=player_font)
                # kpm
                kpm = player_stat_data['basicStats']["kpm"]
                KPM_counter1 += kpm
                draw.text((740, 155 + i * 23), f'{kpm}', fill=max_level_color if kpm >= 2 else 'white', anchor="ra",
                        font=player_font)
                # 时长
                time_played = "{:.1f}".format(player_stat_data['basicStats']["timePlayed"] / 3600)
                TIME_counter1 += float(time_played)
                draw.text((850, 155 + i * 23), f"{time_played}", anchor="ra",
                        fill=max_level_color if float(time_played) >= 1000 else 'white',
                        font=player_font)
            except:
                pass

        # x相差860

        KD_counter2 = 0
        KPM_counter2 = 0
        RANK_counter2 = 0
        TIME_counter2 = 0
        WIN_counter2 = 0
        # 队伍2
        # 队伍2图片
        IMG.paste(team2_pic, (960, 101))
        # 队伍2名
        draw.text((1012, 105), team2_name, fill='white', font=team_font)
        draw.text((1380, 113), f"胜率", fill='white', font=title_font_small)
        draw.text((1470, 113), f"K/D", fill='white', font=title_font_small)
        draw.text((1560, 113), f"KPM", fill='white', font=title_font_small)
        draw.text((1650, 113), f"时长(h)", fill='white', font=title_font_small)
        draw.text((1750, 113), f"延迟", fill='white', font=title_font_small)
        # 队伍2横线
        draw.line([960, 141, 1810, 141], fill=(114, 114, 114), width=2, joint=None)
        # 队伍2竖线
        draw.line([960, 155, 960, 915], fill=(114, 114, 114), width=2, joint=None)
        leve_position_2 = None
        for i, player_item in enumerate(response_data["teams"][1]["players"]):
            # 序号
            draw.text((995, 156 + i * 23), f"{int(i + 1 + server_info['serverInfo']['slots']['Soldier']['max'] / 2)}",
                    anchor="ra", fill='white', font=player_font)
            # 等级框 30*15 等级居中显示
            draw.rectangle([1015, 159 + i * 23, 1045, 173.5 + i * 23],
                        fill=max_level_color if player_item['rank'] == 150 else None, outline=None, width=1)
            RANK_counter2 += player_item['rank']
            if player_item['rank'] == 150:
                max_level_counter += 1
            rank_font_temp = ImageFont.truetype(font_path, 15)
            ascent, descent = rank_font_temp.getsize(f"{player_item['rank']}")
            leve_position_2 = 1030 - ascent / 2, 165.5 + i * 23 - descent / 2
            draw.text(leve_position_2, f"{player_item['rank']}",
                    fill="white",
                    font=rank_font)
            # 战队 名字
            color_temp = 'white'
            if str(player_item["name"]).upper() in bind_pid_list:
                color_temp = bind_color
                bind_counter += 1
            if str(player_item["player_id"]) in vip_pid_list:
                color_temp = vip_color
                vip_counter += 1
            if str(player_item["player_id"]) in admin_pid_list:
                color_temp = admin_color
                admin_counter += 1
            if player_item["platoon"] != "":
                draw.text((1055, 155 + i * 23), f"[{player_item['platoon']}]{player_item['name']}", fill=color_temp,
                        font=player_font)
            else:
                draw.text((1055, 155 + i * 23), player_item["name"], fill=color_temp, font=player_font)
            # 延迟 靠右显示
            ping_pic = Ping5
            if player_item['latency'] <= 50:
                ping_pic = Ping1
            elif 50 < player_item['latency'] <= 100:
                ping_pic = Ping2
            elif 100 < player_item['latency'] <= 150:
                ping_pic = Ping3
            elif 150 < player_item['latency']:
                ping_pic = Ping4
            IMG.paste(ping_pic, (1740, 158 + i * 23), ping_pic)
            draw.text((1790, 155 + i * 23), f"{player_item['latency']}", anchor="ra", fill='white', font=player_font)
            # 生涯数据
            try:
                player_stat_data = scrape_index_tasks_t2[i].result()["result"]
                # 胜率
                win_p = int(player_stat_data['basicStats']['wins'] / (
                        player_stat_data['basicStats']['losses'] + player_stat_data['basicStats']['wins']) * 100)
                WIN_counter2 += win_p
                draw.text((1425, 155 + i * 23), f'{win_p}%', anchor="ra", fill=max_level_color if win_p >= 70 else 'white',
                        font=player_font)
                # kd
                kd = player_stat_data['kdr']
                KD_counter2 += kd
                draw.text((1505, 155 + i * 23), f'{kd}', anchor="ra", fill=max_level_color if kd >= 3 else 'white',
                        font=player_font)
                # kpm
                kpm = player_stat_data['basicStats']["kpm"]
                KPM_counter2 += kpm
                draw.text((1600, 155 + i * 23), f'{kpm}', fill=max_level_color if kpm >= 2 else 'white', anchor="ra",
                        font=player_font)
                # 时长
                time_played = "{:.1f}".format(player_stat_data['basicStats']["timePlayed"] / 3600)
                TIME_counter2 += float(time_played)
                draw.text((1710, 155 + i * 23), f"{time_played}", anchor="ra",
                        fill=max_level_color if float(time_played) >= 1000 else 'white',
                        font=player_font)
            except:
                pass

        i_temp = len(response_data['teams'][0]['players']) if len(response_data['teams'][0]['players']) >= len(
            response_data['teams'][1]['players']) else len(response_data['teams'][1]['players'])
        avg_color = (250, 183, 39)
        avg_1_1 = 0
        avg_1_2 = 0
        avg_1_3 = 0
        avg_1_4 = 0
        avg_1_5 = 0
        if len(response_data['teams'][0]['players']) != 0:
            avg_1_1 = int(RANK_counter1 / len(response_data['teams'][0]['players']))
            avg_1_2 = KD_counter1 / len(response_data['teams'][0]['players'])
            avg_1_3 = KPM_counter1 / len(response_data['teams'][0]['players'])
            avg_1_4 = TIME_counter1 / len(response_data['teams'][0]['players'])
            avg_1_5 = int(WIN_counter1 / len(response_data['teams'][0]['players']))
        avg_2_1 = 0
        avg_2_2 = 0
        avg_2_3 = 0
        avg_2_4 = 0
        avg_2_5 = 0
        if len(response_data['teams'][1]['players']) != 0:
            avg_2_1 = int(RANK_counter2 / len(response_data['teams'][1]['players']))
            avg_2_2 = KD_counter2 / len(response_data['teams'][1]['players'])
            avg_2_3 = KPM_counter2 / len(response_data['teams'][1]['players'])
            avg_2_4 = TIME_counter2 / len(response_data['teams'][1]['players'])
            avg_2_5 = int(WIN_counter2 / len(response_data['teams'][1]['players']))

        if leve_position_1:
            rank_font_temp = ImageFont.truetype(font_path, 15)
            ascent, descent = rank_font_temp.getsize(f"{int(RANK_counter1 / len(response_data['teams'][0]['players']))}")
            leve_position_1 = 168 - ascent / 2, 156 + i_temp * 23
            draw.text((115, 156 + i_temp * 23), f"平均:",
                    fill="white",
                    font=player_font)
            if RANK_counter1 != 0:
                draw.text(leve_position_1, f"{int(RANK_counter1 / len(response_data['teams'][0]['players']))}",
                        fill=avg_color if avg_1_1 > avg_2_1 else "white",
                        font=player_font)
            if WIN_counter1 != 0:
                draw.text((565, 156 + i_temp * 23), f"{int(WIN_counter1 / len(response_data['teams'][0]['players']))}%",
                        anchor="ra",
                        fill=avg_color if avg_1_5 > avg_2_5 else "white",
                        font=player_font)
            if KD_counter1 != 0:
                draw.text((645, 156 + i_temp * 23),
                        "{:.2f}".format(KD_counter1 / len(response_data['teams'][0]['players'])),
                        anchor="ra",
                        fill=avg_color if avg_1_2 > avg_2_2 else "white",
                        font=player_font)
            if KPM_counter1 != 0:
                draw.text((740, 156 + i_temp * 23),
                        "{:.2f}".format(KPM_counter1 / len(response_data['teams'][0]['players'])),
                        anchor="ra",
                        fill=avg_color if avg_1_3 > avg_2_3 else "white",
                        font=player_font)
            if TIME_counter1 != 0:
                draw.text((850, 156 + i_temp * 23),
                        "{:.1f}".format(TIME_counter1 / len(response_data['teams'][0]['players'])),
                        anchor="ra",
                        fill=avg_color if avg_1_4 > avg_2_4 else "white",
                        font=player_font)

        if leve_position_2:
            rank_font_temp = ImageFont.truetype(font_path, 15)
            ascent, descent = rank_font_temp.getsize(f"{int(RANK_counter1 / len(response_data['teams'][1]['players']))}")
            leve_position_2 = 1028 - ascent / 2, 156 + i_temp * 23
            draw.text((975, 156 + i_temp * 23), f"平均:",
                    fill="white",
                    font=player_font)
            if RANK_counter2 != 0:
                draw.text(leve_position_2, f"{int(RANK_counter2 / len(response_data['teams'][1]['players']))}",
                        fill=avg_color if avg_1_1 < avg_2_1 else "white",
                        font=player_font)
            if WIN_counter2 != 0:
                draw.text((1425, 156 + i_temp * 23), f"{int(WIN_counter2 / len(response_data['teams'][1]['players']))}%",
                        anchor="ra",
                        fill=avg_color if avg_1_5 < avg_2_5 else "white",
                        font=player_font)
            if KD_counter2 != 0:
                draw.text((1505, 156 + i_temp * 23),
                        "{:.2f}".format(KD_counter2 / len(response_data['teams'][1]['players'])),
                        anchor="ra",
                        fill=avg_color if avg_1_2 < avg_2_2 else "white",
                        font=player_font)
            if KPM_counter2 != 0:
                draw.text((1600, 156 + i_temp * 23),
                        "{:.2f}".format(KPM_counter2 / len(response_data['teams'][1]['players'])),
                        anchor="ra",
                        fill=avg_color if avg_1_3 < avg_2_3 else "white",
                        font=player_font)
            if TIME_counter2 != 0:
                draw.text((1710, 156 + i_temp * 23),
                        "{:.1f}".format(TIME_counter2 / len(response_data['teams'][1]['players'])),
                        anchor="ra",
                        fill=avg_color if avg_1_4 < avg_2_4 else "white",
                        font=player_font)

        # 服务器信息
        server_info_text = f'服务器状态:{server_info["serverInfo"]["mapModePretty"]}-{server_info["serverInfo"]["mapNamePretty"]}  ' \
                        f'在线人数:{server_info["serverInfo"]["slots"]["Soldier"]["current"]}/{server_info["serverInfo"]["slots"]["Soldier"]["max"]}' \
                        f'[{server_info["serverInfo"]["slots"]["Queue"]["current"]}]({server_info["serverInfo"]["slots"]["Spectator"]["current"]})  ' \
                        f"收藏:{server_info['serverInfo']['serverBookmarkCount']}"

        draw.text((240, 925), server_info_text, fill="white", font=info_font)

        # 服务器简介
        server_dscr = f'        {server_info["serverInfo"]["description"]}'
        test_temp = ""
        i = 0
        for letter in server_dscr:
            if i * 11 % 125 == 0 or (i + 1) * 11 % 125 == 0:
                test_temp += '\n'
                i = 0
            i += get_width(ord(letter))
            test_temp += letter
        draw.text((240, 955), f"服务器简介:{test_temp}", fill="white", font=info_font)

        # 颜色标识
        # 管理
        draw.rectangle([1100, 925, 1120, 945], fill=admin_color, outline=None, width=1)
        draw.text((1130, 925), f"在线管理:{admin_counter}", fill="white", font=player_font)
        # vip
        draw.rectangle([1250, 925, 1270, 945], fill=vip_color, outline=None, width=1)
        draw.text((1280, 925), f"在线VIP:{vip_counter}", fill="white", font=player_font)
        # 群友
        draw.rectangle([1400, 925, 1420, 945], fill=bind_color, outline=None, width=1)
        draw.text((1430, 925), f"在线群友:{bind_counter}", fill="white", font=player_font)
        # 150数量
        draw.rectangle([1550, 925, 1570, 945], fill=max_level_color, outline=None, width=1)
        draw.text((1580, 925), f"150数量:{max_level_counter}", fill="white", font=player_font)

        # 水印
        draw.text((1860, 1060), f"by.13", fill=(114, 114, 114), font=player_font)
        logger.info(f"玩家列表pic耗时:{time.time() - time_start}")
        img = IMG #pil合成的对象
        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        imgByte = io.BytesIO(imgByteArr.getvalue())
        img_url = await bot.client.create_asset(imgByte)
        await msg.reply(img_url,type=MessageTypes.IMG)
    except Exception as e:
        logger.exception(e)

   
# TODO 6.绑定
@bot.command(name='Bind',aliases=['bind', '绑定'])
async def Bind(msg:Message, player_name: str):
    if player_name is None:
        await msg.reply(
            "你不告诉我游戏名字绑啥呢\n示例:/绑定 <你的游戏名字>"
        )
        return False
    player_name = player_name.replace("+", "").replace(" ", "").replace("<", "").replace(">", "")
    # noinspection PyBroadException
    try:
        player_info = await getPid_byName(player_name)
    except Exception as e:
        logger.error(e)
        await msg.reply(
            f"网络出错，请稍后再试"
        )
        return False
    if player_info['personas'] == {}:
        await msg.reply(
            f"玩家[{player_name}]不存在"
        )
        return False
    # 创建配置文件
    record.config_bind(msg.author_id)
    # 写入绑定信息
    with open(f"app/data/battlefield/binds/players/{msg.author_id}/bind.json", 'w', encoding='utf-8') as file_temp1:
        json.dump(player_info, file_temp1, indent=4)
        await msg.reply(
            f"绑定成功!你的信息如下:\n"
            f"Name:{player_info['personas']['persona'][0]['displayName']}\nId:{player_info['personas']['persona'][0]['personaId']}\nuid:{player_info['personas']['persona'][0]['pidId']}"
        )
        # 调用战地查询计数器，绑定记录增加
        record.bind_counter(msg.author_id, f"{player_info['personas']['persona'][0]['pidId']}-{player_info['personas']['persona'][0]['displayName']}")
        # 初始化玩家数据
        scrape_index_tasks = [
            asyncio.ensure_future(InfoCache_stat(str(player_info['personas']['persona'][0]['personaId'])).get_data()),
            asyncio.ensure_future(InfoCache_weapon(str(player_info['personas']['persona'][0]['personaId'])).get_data()),
            asyncio.ensure_future(InfoCache_vehicle(str(player_info['personas']['persona'][0]['personaId'])).get_data())
        ]
        # noinspection PyBroadException
        try:
            tasks = asyncio.gather(*scrape_index_tasks)
            await tasks
        except Exception as e:
            logger.error(e)
@bot.command(name='weapon',aliases=['weapon', '武器',"手枪","半自动","步枪","冲锋枪","霰弹枪","手雷","精英兵","驾驶员","近战","配备","机枪"])
async def weapon(msg:Message,player_name: str=None):
    # 判断玩家名字存不存在
    # noinspection PyBroadException
    if player_name!=None :
        try:
            player_info = await getPid_byName(player_name)
        except Exception as e:
            logger.error(e)
            await msg.reply(f"网络出错，请稍后再试")
            return False
        if player_info['personas'] == {}:
            await msg.reply(
                f"玩家[{player_name}]不存在"
            )
            return False
        else:
            player_pid = player_info['personas']['persona'][0]['personaId']
            player_name = player_info['personas']['persona'][0]['displayName']
        # 检查绑定没有,没有绑定则终止，绑定了就读缓存的pid
    else:
        if not record.check_bind(msg.author_id):
            await msg.reply(
                f"请先使用'\绑定+你的游戏名字'进行绑定\n例如:\绑定 xxx")
            return False
        else:
            # noinspection PyBroadException
            try:
                player_pid = record.get_bind_pid(msg.author_id)
                player_name = record.get_bind_name(msg.author_id)
            except Exception as e:
                logger.error(e)
                await msg.reply("绑定信息过期,请重新绑定!")
                return
    start_time = time.time()
    # noinspection PyBroadException
    try:
        # weapon_data = await get_weapon_data(str(player_pid))
        # noinspection PyBroadException
        try:
            weapon_data = await InfoCache_weapon(str(player_pid)).get_data()
        except Exception as e:
            logger.error(e)
            await InfoCache_weapon(str(player_pid)).update_cache()
            weapon_data = await InfoCache_weapon(str(player_pid)).get_data()
        item_temp = weapon_data["result"][11]["weapons"].pop()
        weapon_data["result"][11]["weapons"].pop()
        weapon_data["result"][3]["weapons"].append(item_temp)
        weapon_data = weapon_data["result"]
    except Exception as e:
        logger.error(e)
        await msg.reply("网络出错请稍后再试!")
        return False
    end_time = time.time()
    logger.info(f"接口耗时:{end_time - start_time}s")
    weapon_temp = {}
    start_time2 = time.time()
    if msg.content.split()[0][1:] in ["武器","weapon"]:
        for item in weapon_data:
            for item2 in item["weapons"]:
                if item2["stats"]["values"] != {}:
                    if item2["stats"]["values"]["kills"] != 0.0:
                        weapon_temp[zhconv.convert(item2["name"], 'zh-cn')] = [
                            int(item2["stats"]["values"]["kills"]),  # 击杀
                            "{:.2f}".format(
                                item2["stats"]["values"]["kills"] / item2["stats"]["values"]["seconds"] * 60) if
                            item2["stats"]["values"]["seconds"] != 0 else "0",  # kpm
                            "{:.2f}%".format(
                                item2["stats"]["values"]["hits"] / item2["stats"]["values"]["shots"] * 100) if
                            item2["stats"]["values"]["shots"] * 100 != 0 else "0",  # 命中率
                            "{:.2f}%".format(
                                item2["stats"]["values"]["headshots"] / item2["stats"]["values"]["kills"] * 100) if
                            item2["stats"]["values"]["kills"] != 0 else "0",  # 爆头率
                            "{:.2f}".format(item2["stats"]["values"]["hits"] / item2["stats"]["values"]["kills"]) if
                            item2["stats"]["values"]["kills"] != 0 else "0",  # 效率
                            "{:.0f}h".format(item2["stats"]["values"]["seconds"] / 3600),  # 游戏时长
                            item2["imageUrl"].replace("[BB_PREFIX]",
                                                      "https://eaassets-a.akamaihd.net/battlelog/battlebinary")
                        ]
    else:
        trdict={"精英兵":"0","轻机枪":"1","机枪":"1","近战":"2","步枪":"3","装备":"4","配备":"4","半自动":"5","手雷": "6","霰弹枪":"8","驾驶员":"9","冲锋枪":"10","手枪": "11"}
        try:
            weapon_type_temp =int(trdict[msg.content.split()[0][1:]])
        except:
            logger.error(msg.content)
            await msg.reply("武器类别不存在")
            return False
        for item2 in weapon_data[weapon_type_temp]["weapons"]:
            if item2["stats"]["values"] != {}:
                weapon_temp[zhconv.convert(item2["name"], 'zh-cn')] = [
                    int(item2["stats"]["values"]["kills"]),  # 击杀
                    "{:.2f}".format(item2["stats"]["values"]["kills"] / item2["stats"]["values"]["seconds"] * 60)
                    if item2["stats"]["values"]["seconds"] != 0
                    else "0",  # kpm
                    "{:.2f}%".format(item2["stats"]["values"]["hits"] / item2["stats"]["values"]["shots"] * 100)
                    if item2["stats"]["values"]["shots"] * 100 != 0
                    else "0",  # 命中率
                    "{:.2f}%".format(item2["stats"]["values"]["headshots"] / item2["stats"]["values"]["kills"] * 100)
                    if item2["stats"]["values"]["kills"] != 0
                    else "0",  # 爆头率
                    "{:.2f}".format(item2["stats"]["values"]["hits"] / item2["stats"]["values"]["kills"])
                    if item2["stats"]["values"]["kills"] != 0
                    else "0",  # 效率
                    "{:.1f}h".format(item2["stats"]["values"]["seconds"] / 3600),  # 游戏时长
                    item2["imageUrl"].replace("[BB_PREFIX]", "https://eaassets-a.akamaihd.net/battlelog/battlebinary")
                    # 图片url
                ]
    weapon_temp_sorted = sorted(weapon_temp.items(), key=lambda x: x[1][0], reverse=True)  # 得到元组列表
    # print(weapon_temp_sorted)
    weapon_list = weapon_temp_sorted[:4]
    weapon1 = []
    weapon2 = []
    weapon3 = []
    weapon4 = []
    weapon123 = [weapon1, weapon2, weapon3, weapon4]
    i = 0
    # noinspection PyBroadException
    try:
        while i <= 3:
            weapon_item = weapon123[i]
            weapon_item.append(weapon_list[i][0])
            weapon_item.append(weapon_list[i][1][0])
            weapon_item.append(weapon_list[i][1][1])
            weapon_item.append(weapon_list[i][1][2])
            weapon_item.append(weapon_list[i][1][3])
            weapon_item.append(weapon_list[i][1][4])
            weapon_item.append(weapon_list[i][1][6])
            weapon_item.append(weapon_list[i][1][5])
            i += 1
    except Exception as e:
        logger.error(e)
        await msg.reply(
        
            "数据不足!"
        )
        return False
    # 头像信息
    # noinspection PyBroadException
    html = None
    if os.path.exists(f"app/data/battlefield/players/{player_pid}/avatar.json"):
        try:
            with open(f"app/data/battlefield/players/{player_pid}/avatar.json", 'r', encoding='utf-8') as file_temp1:
                html = json.load(file_temp1)
                if html is None:
                    raise Exception
                if "avatar" not in html:
                    raise Exception
        except Exception as e:
            logger.warning(f"未找到玩家{player_name}头像缓存,开始下载{e}")
    if html is None:
        # noinspection PyBroadException
        try:
            # async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.gametools.network/bf1/player?name=' + str(player_name) + '&platform=pc', timeout=3)
            html = eval(response.text)
            if "avatar" not in html:
                raise Exception
            if not os.path.exists(f"app/data/battlefield/players/{player_pid}"):
                os.makedirs(f"app/data/battlefield/players/{player_pid}")
            with open(f"app/data/battlefield/players/{player_pid}/avatar.json", 'w', encoding='utf-8') as file_temp1:
                json.dump(html, file_temp1, indent=4)
        except Exception as e:
            logger.error(e)
            await msg.reply(
                "网络出错请稍后再试!"
            )
            return False
    end_time2 = time.time()
    logger.info(f'接口2耗时:{end_time2 - start_time2}')
    start_time3 = time.time()

    # 底图选择
    # bg_img = Image.open(await pic_custom(player_pid))
    try:
        bg_img = Image.open(bg_pic.choose_bg(player_pid, "weapon"))
        width, height = bg_img.size
        if not (width == 1080 and height == 2729):
            b1 = width / 1080
            b2 = height / 2729
            if b1 < 1 or b2 < 1:
                倍数 = 1 / b1 if 1 / b1 > 1 / b2 else 1 / b2
            else:
                倍数 = b1 if b1 < b2 else b2
            # 放大图片
            bg_img = bg_img.resize((int(width * 倍数) + 1, int(height * 倍数) + 1), Image.ANTIALIAS)
            # 裁剪到中心位置
            width, height = bg_img.size
            left = (width - 1080) / 2
            top = (height - 2729) / 2
            right = (width + 1080) / 2
            bottom = (height + 2729) / 2
            bg_img = bg_img.crop((left, top, right, bottom))
            底图 = Image.open(f"app/data/battlefield/pic/bg/底图.png").convert('RGBA')
            bg_img.paste(底图, (0, 0), 底图)
        draw = ImageDraw.Draw(bg_img)
        # 字体路径
        font_path = 'app/data/battlefield/font/BFText-Regular-SC-19cf572c.ttf'
        title_font = ImageFont.truetype(font_path, 50)
        star_font = ImageFont.truetype(font_path, 45)
        time_font = ImageFont.truetype(font_path, 25)
        name_font = ImageFont.truetype(font_path, 45)
        content_font = ImageFont.truetype(font_path, 40)
        SavePic = f"app/data/battlefield/Temp/{player_pid}.png"
        # 玩家头像获取
        player_img = await playerPicDownload(html["avatar"], html["userName"])
        # 玩家头像打开
        avatar_img = Image.open(player_img).convert('RGBA')
        # 玩家头像拼接
        bg_img.paste(avatar_img, (64, 91))
        # 玩家ID拼接
        draw.text((300, 225), "ID:%s" % html["userName"], fill='white', font=title_font)
        # 时间拼接
        time_now = time.strftime("%Y/%m/%d-%H:%M", time.localtime(time.time()))
        draw.text((790, 260), time_now, fill='white', font=time_font)
        for i in range(4):
            # 间距 623
            # 武器图片获取
            pic_url = await PicDownload(weapon123[i][6])
            # 打开武器图像
            weapon_png = Image.open(pic_url).convert('RGBA')
            # 拉伸
            weapon_png = weapon_png.resize((588, 147))
            star = str(int(weapon123[i][1] / 100))
            weapons_star = "★"
            # tx_img = Image.open("")
            if weapon123[i][1] >= 10000:
                # 金色
                tx_img = Image.open("app/data/battlefield/pic/tx/" + "1.png").convert(
                    'RGBA')
                tx_img = tx_img.resize((267, 410))
                bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
                draw.text((179, 506 + i * 580), weapons_star, font=star_font, fill=(255, 132, 0))
                draw.text((233, 509 + i * 580), star, font=star_font, fill=(255, 132, 0))
            elif 6000 <= weapon123[i][1] < 10000:
                # 蓝色
                tx_img = Image.open("app/data/battlefield/pic/tx/" + "2.png").convert(
                    'RGBA')
                tx_img = tx_img.resize((267, 410))
                bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
                draw.text((179, 506 + i * 580), weapons_star, font=star_font, fill=(74, 151, 255))
                draw.text((233, 509 + i * 580), star, font=star_font, fill=(74, 151, 255))
            elif 4000 <= weapon123[i][1] < 6000:
                # 白色
                tx_img = Image.open("app/data/battlefield/pic/tx/" + "3.png").convert(
                    'RGBA')
                tx_img = tx_img.resize((267, 410))
                bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
                draw.text((179, 506 + i * 580), weapons_star, font=star_font)
                draw.text((233, 509 + i * 580), star, font=star_font)
            elif 0 <= weapon123[i][1] < 4000:
                draw.text((179, 506 + i * 580), weapons_star, font=star_font)
                draw.text((233, 509 + i * 580), star, font=star_font)
            # 武器图像拼接
            bg_img.paste(weapon_png, (250, 392 + i * 580), weapon_png)
            draw.text((210, 630 + i * 580), weapon123[i][0], font=name_font)
            draw.text((210, 730 + i * 580), "击杀:%d" % weapon123[i][1], font=content_font)
            draw.text((600, 730 + i * 580), "kpm:%s" % weapon123[i][2], font=content_font)
            draw.text((210, 780 + i * 580), "命中率:%s" % weapon123[i][3], font=content_font)
            draw.text((600, 780 + i * 580), "爆头率:%s" % weapon123[i][4], font=content_font)
            draw.text((210, 830 + i * 580), "效率:%s" % weapon123[i][5], font=content_font)
            draw.text((600, 830 + i * 580), "时长:%s" % weapon123[i][7], font=content_font)
        bg_img = bg_img.convert('RGB')
    except Exception as e:
        logger.error(e)
    end_time3 = time.time()
    logger.info(f'画图耗时:{end_time3 - start_time3}')
    logger.info(f"制图总耗时:{end_time3 - start_time}秒")
    start_time4 = time.time()
    img = bg_img #pil合成的对象
    imgByteArr = io.BytesIO()
    img.save(imgByteArr, format='PNG')
    imgByte = io.BytesIO(imgByteArr.getvalue())
    img_url = await bot.client.create_asset(imgByte)
    await msg.reply(img_url,type=MessageTypes.IMG)
    end_time4 = time.time()
    logger.info(f"发送耗时:{end_time4 - start_time4}秒")
    if end_time4 - start_time4 > 60:
        await msg.reply(
            f"发送耗时:{int(end_time4 - start_time4)}秒,似乎被限制了呢"
        )
    # noinspection PyBroadException
    # 武器计数器
    record.weapon_counter(msg.author_id, str(player_pid), str(player_name), msg.content.split()[0][1:])
    return True
@bot.command(name='vehicle',aliases=["载具", "地面", "陆地", "空中", "飞机", "海上", "海洋", "定点", "巨兽"])
async def vehicle(msg:Message,player_name: str=None):
    if player_name!=None:
        try:
            player_info = await getPid_byName(player_name)
        except Exception as e:
            logger.error(e)
            await msg.reply(
                f"网络出错，请稍后再试"
            )
            return False
        if player_info['personas'] == {}:
            await msg.reply(
                f"玩家[{player_name}]不存在"
            )
            return False
        else:
            player_pid = player_info['personas']['persona'][0]['personaId']
            player_name = player_info['personas']['persona'][0]['displayName']
    else:
        # 检查绑定没有,没有绑定则终止，绑定了就读缓存的pid
        if not record.check_bind(msg.author_id):
            await msg.reply(
                f"请先使用'/绑定+你的游戏名字'进行绑定\n例如:/绑定 xxx"
            )
            return False
        else:
            # noinspection PyBroadException
            try:
                player_pid = record.get_bind_pid(msg.author_id)
                player_name = record.get_bind_name(msg.author_id)
            except Exception as e:
                logger.error(e)
                await msg.reply(
                
                    "绑定信息过期,请重新绑定!"
                )
                return
    start_time = time.time()
    # noinspection PyBroadException
    try:
        # vehicle_data = await get_vehicle_data(str(player_pid))
        # vehicle_data = await InfoCache(str(player_pid), "vehicle").get_data()
        # noinspection PyBroadException
        try:
            vehicle_data = await InfoCache_vehicle(str(player_pid)).get_data()
        except Exception as e:
            logger.error(e)
            await InfoCache_vehicle(str(player_pid)).update_cache()
            vehicle_data = await InfoCache_vehicle(str(player_pid)).get_data()
        vehicle_data = vehicle_data["result"]
    except Exception as e:
        logger.error(e)
        await msg.reply(
        
            "网络出错请稍后再试!"
        )
        return False
    end_time = time.time()
    logger.info(f"接口耗时:{end_time - start_time}s")
    vehicle_temp = {}
    start_time2 = time.time()
    if msg.content.split()[0][1:] in ["载具", "vehicle"]:
        for item1 in vehicle_data:
            for item2 in item1["vehicles"]:
                vehicle_temp[zhconv.convert(item2["name"], 'zh-cn')] = [
                    int(item2["stats"]["values"]["kills"]),  # 击杀
                    "{:.2f}".format(item2["stats"]["values"]["kills"] / item2["stats"]["values"]["seconds"] * 60)
                    if item2["stats"]["values"]["seconds"] != 0 else "0",
                    # kpm
                    int(item2["stats"]["values"]["destroyed"]),  # 摧毁
                    "{:.2f}h".format(item2["stats"]["values"]["seconds"] / 3600),  # 时长
                    item2["imageUrl"].replace("[BB_PREFIX]", "https://eaassets-a.akamaihd.net/battlelog/battlebinary")
                    # 图片url
                ]
    else:
        vehicle_type_list = [["重型坦克", "巡航坦克", "輕型坦克", "火砲裝甲車", "攻擊坦克", "突擊裝甲車", "地面載具", "马匹"],
                             ["攻擊機", "轟炸機", "戰鬥機", "重型轟炸機", "飛船"],
                             ["船隻", "驅逐艦"],
                             ["定點武器"],
                             ["機械巨獸"]]
        if msg.content.split()[0][1:] in ["地面", "陆地"]:
            vehicle_type_list = vehicle_type_list[0]
        elif msg.content.split()[0][1:] in ["空中", "飞机"]:
            vehicle_type_list = vehicle_type_list[1]
        elif msg.content.split()[0][1:] in ["海上", "海洋"]:
            vehicle_type_list = vehicle_type_list[2]
        elif msg.content.split()[0][1:] in ["定点"]:
            vehicle_type_list = vehicle_type_list[3]
        elif msg.content.split()[0][1:] in ["巨兽"]:
            vehicle_type_list = vehicle_type_list[4]
        for item1 in vehicle_data:
            if item1["name"] in vehicle_type_list:
                for item2 in item1["vehicles"]:
                    vehicle_temp[zhconv.convert(item2["name"], 'zh-cn')] = [
                        int(item2["stats"]["values"]["kills"]),  # 击杀
                        "{:.2f}".format(
                            item2["stats"]["values"]["kills"] / item2["stats"]["values"]["seconds"] * 60) if
                        item2["stats"]["values"]["seconds"] != 0 else "0",
                        # kpm
                        int(item2["stats"]["values"]["destroyed"]),  # 摧毁
                        "{:.1f}h".format(item2["stats"]["values"]["seconds"] / 3600),  # 时长
                        item2["imageUrl"].replace("[BB_PREFIX]",
                                                  "https://eaassets-a.akamaihd.net/battlelog/battlebinary")  # 图片url
                    ]
                if vehicle_type_list == ["船隻", "驅逐艦"]:
                    item_temp = vehicle_data[15]["vehicles"][2]
                    vehicle_temp[zhconv.convert(item_temp["name"], 'zh-cn')] = [
                        int(item_temp["stats"]["values"]["kills"]),  # 击杀
                        "{:.2f}".format(
                            item_temp["stats"]["values"]["kills"] / item_temp["stats"]["values"]["seconds"] * 60) if
                        item_temp["stats"]["values"]["seconds"] != 0 else "0",
                        # kpm
                        int(item_temp["stats"]["values"]["destroyed"]),  # 摧毁
                        "{:.1f}h".format(item_temp["stats"]["values"]["seconds"] / 3600),  # 时长
                        item_temp["imageUrl"].replace("[BB_PREFIX]",
                                                      "https://eaassets-a.akamaihd.net/battlelog/battlebinary")
                        # 图片url
                    ]
    vehicle_temp_sorted = sorted(vehicle_temp.items(), key=lambda x: x[1][0], reverse=True)  # 得到元组列表
    # print(weapon_temp_sorted)
    vehicle_list = vehicle_temp_sorted[:4]
    vehicle1 = []
    vehicle2 = []
    vehicle3 = []
    vehicle4 = []
    vehicle123 = [vehicle1, vehicle2, vehicle3, vehicle4]
    i = 0
    while i <= 3:
        vehicle_temp = vehicle123[i]
        vehicle_temp.append(vehicle_list[i][0])
        vehicle_temp.append(vehicle_list[i][1][0])
        vehicle_temp.append(vehicle_list[i][1][1])
        vehicle_temp.append(vehicle_list[i][1][2])
        vehicle_temp.append(vehicle_list[i][1][3])
        vehicle_temp.append(vehicle_list[i][1][4])
        i += 1
    # 头像信息
    # noinspection PyBroadException
    html = None
    if os.path.exists(f"app/data/battlefield/players/{player_pid}/avatar.json"):
        try:
            with open(f"app/data/battlefield/players/{player_pid}/avatar.json", 'r', encoding='utf-8') as file_temp1:
                html = json.load(file_temp1)
                if html is None:
                    raise Exception
                if "avatar" not in html:
                    raise Exception
        except Exception as e:
            logger.warning(f"未找到玩家{player_name}头像缓存,开始下载{e}")
    if html is None:
        # noinspection PyBroadException
        try:
            # async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.gametools.network/bf1/player?name=' + str(player_name) + '&platform=pc', timeout=3)
            html = eval(response.text)
            if "avatar" not in html:
                raise Exception
            if not os.path.exists(f"app/data/battlefield/players/{player_pid}"):
                os.makedirs(f"app/data/battlefield/players/{player_pid}")
            with open(f"app/data/battlefield/players/{player_pid}/avatar.json", 'w', encoding='utf-8') as file_temp1:
                json.dump(html, file_temp1, indent=4)
        except Exception as e:
            logger.error(e)
            await msg.reply(
            
                "网络出错请稍后再试!"
            )
            return False
    end_time2 = time.time()
    logger.info(f'接口2耗时:{end_time2 - start_time2}')
    start_time3 = time.time()
    # 底图选择
    # bg_img = Image.open(await pic_custom(player_pid))
    bg_img = Image.open(bg_pic.choose_bg(player_pid, "weapon"))
    width, height = bg_img.size
    if not (width == 1080 and height == 2729):
        b1 = width / 1080
        b2 = height / 2729
        if b1 < 1 or b2 < 1:
            倍数 = 1 / b1 if 1 / b1 > 1 / b2 else 1 / b2
        else:
            倍数 = b1 if b1 < b2 else b2
        # 放大图片
        bg_img = bg_img.resize((int(width * 倍数) + 1, int(height * 倍数) + 1), Image.ANTIALIAS)
        # 裁剪到中心位置
        width, height = bg_img.size
        left = (width - 1080) / 2
        top = (height - 2729) / 2
        right = (width + 1080) / 2
        bottom = (height + 2729) / 2
        bg_img = bg_img.crop((left, top, right, bottom))
        底图 = Image.open(f"app/data/battlefield/pic/bg/底图.png").convert('RGBA')
        bg_img.paste(底图, (0, 0), 底图)
    draw = ImageDraw.Draw(bg_img)
    # 字体路径
    font_path = 'app/data/battlefield/font/BFText-Regular-SC-19cf572c.ttf'
    title_font = ImageFont.truetype(font_path, 50)
    star_font = ImageFont.truetype(font_path, 45)
    time_font = ImageFont.truetype(font_path, 25)
    name_font = ImageFont.truetype(font_path, 45)
    content_font = ImageFont.truetype(font_path, 40)
    SavePic = "app/data/battlefield/Temp/" + str(int(time.time())) + ".png"
    # 玩家头像获取
    player_img = await playerPicDownload(html["avatar"], html["userName"])
    # 玩家头像打开
    avatar_img = Image.open(player_img).convert('RGBA')
    # 玩家头像拼接
    bg_img.paste(avatar_img, (64, 91))
    # 玩家ID拼接
    draw.text((300, 225), "ID:%s" % html["userName"], fill='white', font=title_font)
    # 时间拼接
    time_now = time.strftime("%Y/%m/%d-%H:%M", time.localtime(time.time()))
    draw.text((790, 260), time_now, fill='white', font=time_font)
    for i in range(4):
        # 间距 623
        # 武器图片获取
        pic_url = await PicDownload(vehicle123[i][5])
        # 打开武器图像
        weapon_png = Image.open(pic_url).convert('RGBA')
        # 拉伸
        weapon_png = weapon_png.resize((563, 140))
        # 星星数
        star = str(int(vehicle123[i][1] / 100))
        weapons_star = "★"
        # tx_img = Image.open("")
        if vehicle123[i][1] >= 10000:
            # 金色
            tx_img = Image.open("app/data/battlefield/pic/tx/" + "1.png").convert(
                'RGBA')
            tx_img = tx_img.resize((267, 410))
            bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
            draw.text((179, 506 + i * 580), weapons_star, font=star_font, fill=(255, 132, 0))
            draw.text((233, 509 + i * 580), star, font=star_font, fill=(255, 132, 0))
        elif 6000 <= vehicle123[i][1] < 10000:
            # 蓝色
            tx_img = Image.open("app/data/battlefield/pic/tx/" + "2.png").convert(
                'RGBA')
            tx_img = tx_img.resize((267, 410))
            bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
            draw.text((179, 506 + i * 580), weapons_star, font=star_font, fill=(74, 151, 255))
            draw.text((233, 509 + i * 580), star, font=star_font, fill=(74, 151, 255))
        elif 4000 <= vehicle123[i][1] < 6000:
            # 白色
            tx_img = Image.open("app/data/battlefield/pic/tx/" + "3.png").convert(
                'RGBA')
            tx_img = tx_img.resize((267, 410))
            bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
            draw.text((179, 506 + i * 580), weapons_star, font=star_font)
            draw.text((233, 509 + i * 580), star, font=star_font)
        elif 0 <= vehicle123[i][1] < 4000:
            draw.text((179, 506 + i * 580), weapons_star, font=star_font)
            draw.text((233, 509 + i * 580), star, font=star_font)
        # 武器图像拼接
        bg_img.paste(weapon_png, (250, 392 + i * 580), weapon_png)
        draw.text((210, 630 + i * 580), vehicle123[i][0], font=name_font)
        draw.text((210, 730 + i * 580), "击杀:%d" % vehicle123[i][1], font=content_font)
        draw.text((600, 730 + i * 580), "kpm：%s" % vehicle123[i][2], font=content_font)
        draw.text((210, 780 + i * 580), "摧毁：%s" % vehicle123[i][3], font=content_font)
        draw.text((600, 780 + i * 580), "时长：%s" % vehicle123[i][4], font=content_font)
    bg_img = bg_img.convert('RGB')
    end_time3 = time.time()
    logger.info(f'画图耗时:{end_time3 - start_time3}')
    start_time4 = time.time()
    img = bg_img #pil合成的对象
    imgByteArr = io.BytesIO()
    img.save(imgByteArr, format='PNG')
    imgByte = io.BytesIO(imgByteArr.getvalue())
    img_url = await bot.client.create_asset(imgByte)
    await msg.reply(img_url,type=MessageTypes.IMG)
    end_time4 = time.time()
    logger.info(f"发送耗时:{end_time4 - start_time4}秒")
    if end_time4 - start_time4 > 60:
        await msg.reply(
            f"发送耗时:{int(end_time4 - start_time4)}秒,似乎被限制了呢= ="
        )
    # 调用载具计数器
    record.vehicle_counter(msg.author_id, str(player_pid), player_name, msg.content.split()[0][1:])
    return True
@bot.command(name='player_stat_pic',aliases=['stat', '生涯'])
async def player_stat_pic(msg:Message, player_name: str=None):
    """
     TODO 4:生涯数据
    :param message:
    :param group:
    :param sender:
    :param app:
    :param player_name: 玩家名字（可选参数
    :return: None
    """
    global client
    start_time = time.time()
    if player_name!=None:
        try:
            player_info = await getPid_byName(player_name)
        except Exception as e:
            logger.error(e)
            await msg.reply(
                f"网络出错，请稍后再试"
            )
            return False
        if player_info['personas'] == {}:
            await msg.reply(
                f"玩家[{player_name}]不存在"
            )
            return False
        else:
            player_pid = player_info['personas']['persona'][0]['personaId']
            player_name = player_info['personas']['persona'][0]['displayName']
    else:
        # 检查绑定没有,没有绑定则终止，绑定了就读缓存的pid
        if not record.check_bind(msg.author_id):
            await msg.reply(
                f"请先使用'/绑定+你的游戏名字'进行绑定\n例如:/绑定 xxx"
            )
            return False
        else:
            # noinspection PyBroadException
            try:
                player_pid = record.get_bind_pid(msg.author_id)
                player_name = record.get_bind_name(msg.author_id)
            except Exception as e:
                logger.error(e)
                await msg.reply(
                
                    "绑定信息过期,请重新绑定!"
                )
                return
    scrape_index_tasks = [
        asyncio.ensure_future(InfoCache_stat(str(player_pid)).get_data()),
        asyncio.ensure_future(InfoCache_weapon(str(player_pid)).get_data()),
        asyncio.ensure_future(InfoCache_vehicle(str(player_pid)).get_data()),
        asyncio.ensure_future(player_stat_bfban_api(player_pid))
    ]
    tasks = asyncio.gather(*scrape_index_tasks)
    # noinspection PyBroadException
    try:
        await tasks
    except Exception as e:
        logger.error(e)
        await msg.reply(
            f"查询时出现网络错误!"
        )
        return False

    # player_stat_data = scrape_index_tasks[0].result()["result"]
    # player_stat_data = (await InfoCache(str(player_pid), "stat").get_data())["result"]
    # noinspection PyBroadException
    try:
        # player_stat_data = (await InfoCache(str(player_pid), "stat").get_data())["result"]
        player_stat_data = scrape_index_tasks[0].result()["result"]
    except Exception as e:
        logger.error(e)
        await InfoCache(str(player_pid), "stat").update_cache()
        try:
            player_stat_data = (await InfoCache_stat(str(player_pid)).get_data())["result"]
        except:
            await msg.reply(
                f"查询时出现网络错误!"
            )
            return False

    # 等级信息
    rank_data = "0"
    if rank_data == "0":
        # noinspection PyBroadException
        try:
            # async with httpx.AsyncClient() as client:
            rank_response = await client.get('https://battlefieldtracker.com/bf1/profile/pc/%s' % player_name,
                                             timeout=1)
            rank_temp = rank_response.text
            if rank_temp == 404:
                pass
            else:
                soup = BeautifulSoup(rank_temp, "html.parser")
                for item in soup.find_all("div", class_="details"):
                    rank_data = re.findall(re.compile(r'<span class="title">Rank (.*?)</span>'), str(item))[0]
                    with open(f"app/data/battlefield/players/{player_pid}/rank.txt", 'w+',
                              encoding='utf-8') as file_temp1:
                        file_temp1.write(rank_temp)
                        logger.success(f"更新玩家{player_name}等级缓存成功")
        except Exception as e:
            logger.warning(f"获取玩家{player_name}等级失败:{e}")
            if os.path.exists(f"app/data/battlefield/players/{player_pid}/"):
                try:
                    with open(f"app/data/battlefield/players/{player_pid}/rank.txt", 'r', encoding='utf-8') as file_temp1:
                        rank_temp = file_temp1.read()
                        soup = BeautifulSoup(rank_temp, "html.parser")
                        for item in soup.find_all("div", class_="details"):
                            rank_data = re.findall(re.compile(r'<span class="title">Rank (.*?)</span>'), str(item))[0]
                except Exception as e:
                    logger.warning(f"未找到玩家{player_name}等级缓存:{e}")
            pass

    # bfban查询
    bf_html = scrape_index_tasks[3].result()
    if type(bf_html) == str:
        if_cheat = False
        bf_url = "暂无信息"
        bfban_status = bf_html
    else:
        bf_stat = bf_html
        if_cheat = False
        stat_dict = {
            "0": "未处理",
            "1": "实锤",
            "2": "嫌疑再观察",
            "3": "认为没开",
            "4": "回收站",
            "5": "回复讨论中",
            "6": "等待管理确认"
        }
        # 先看下有无案件信息
        if "url" in bf_stat["personaids"][str(player_pid)]:
            bf_url = bf_stat["personaids"][str(player_pid)]["url"]
            bfban_status = stat_dict[str(bf_stat["personaids"][str(player_pid)]["status"])]
            if bf_stat["personaids"][str(player_pid)]["hacker"]:
                if_cheat = True
        else:
            bf_url = "暂无信息"
            bfban_status = "未查询到联ban信息"
    # 头像信息
    # noinspection PyBroadException
    html = None
    if os.path.exists(f"app/data/battlefield/players/{player_pid}/avatar.json"):
        try:
            with open(f"app/data/battlefield/players/{player_pid}/avatar.json", 'r', encoding='utf-8') as file_temp1:
                html = json.load(file_temp1)
                if html is None:
                    raise Exception
                if "avatar" not in html:
                    raise Exception
        except Exception as e:
            logger.warning(f"未找到玩家{player_name}头像缓存,开始下载\n{e}")
    if html is None:
        # noinspection PyBroadException
        try:
            # async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.gametools.network/bf1/player?name=' + str(player_name) + '&platform=pc', timeout=3)
            html = eval(response.text)
            if "avatar" not in html:
                raise Exception
            if not os.path.exists(f"app/data/battlefield/players/{player_pid}"):
                os.makedirs(f"app/data/battlefield/players/{player_pid}")
            with open(f"app/data/battlefield/players/{player_pid}/avatar.json", 'w', encoding='utf-8') as file_temp1:
                json.dump(html, file_temp1, indent=4)
        except Exception as e:
            logger.error(e)
            await msg.reply(
            
                "网络出错请稍后再试!"
            )
            return False
    # print(type(html))
    # 头像 姓名 等级 技巧值 KD 步战kd  击杀 死亡 spm kpm 胜率 命中率 爆头率 最远爆头距离 游戏时长
    """
    对应数据类型：
        <class 'str'><class 'str'><class 'int'><class 'float'><class 'float'><class 'float'><class 'int'><class 'int'>
        <class 'float'><class 'float'><class 'str'><class 'str'><class 'str'><class 'float'><class 'str'>
    """

    vehicle_kill = 0
    for item in player_stat_data["vehicleStats"]:
        vehicle_kill += item["killsAs"]
    infantry_kill = player_stat_data['basicStats']['kills'] - vehicle_kill

    data_list = [
        html["avatar"], player_name, rank_data, player_stat_data["basicStats"]["skill"],
        player_stat_data['kdr'],  # 4
        "{:.2f}".format(infantry_kill / player_stat_data['basicStats']["deaths"]) if
        player_stat_data['basicStats']["deaths"] != 0 else infantry_kill,
        player_stat_data['basicStats']['kills'],
        player_stat_data['basicStats']["deaths"], player_stat_data['basicStats']["spm"],  # 8
        player_stat_data['basicStats']["kpm"], "{:.2f}%".format(player_stat_data['basicStats']['wins'] / (
                player_stat_data['basicStats']['losses'] + player_stat_data['basicStats']['wins']) * 100)
        if (player_stat_data['basicStats']['losses'] + player_stat_data['basicStats']['wins']) != 0 else "0",
        # 10
        player_stat_data["accuracyRatio"] * 100, "{:.2f}%".format(
            player_stat_data["headShots"] / player_stat_data['basicStats']['kills'] * 100) if
        player_stat_data['basicStats']['kills'] != 0 else "0%",
        player_stat_data["longestHeadShot"],
        player_stat_data['basicStats']["timePlayed"] / 3600, if_cheat,
        # 15
        0, player_stat_data['basicStats']["wins"], player_stat_data['basicStats']["losses"],
        player_stat_data["favoriteClass"], player_stat_data['killAssists'],  # 20
        player_stat_data["revives"], player_stat_data["repairs"], player_stat_data["highestKillStreak"],
        player_stat_data["heals"], player_stat_data["dogtagsTaken"]
    ]

    data_list[2] = rank_data

    # 武器数据
    # noinspection PyBroadException
    try:
        # noinspection PyBroadException
        try:
            # weapon_data = await InfoCache(str(player_pid), "weapon").get_data()
            weapon_data = scrape_index_tasks[1].result()
        except Exception as e:
            logger.error(e)
            await InfoCache(str(player_pid), "weapon").update_cache()
            weapon_data = await InfoCache(str(player_pid), "weapon").get_data()
        item_temp = weapon_data["result"][11]["weapons"].pop()
        weapon_data["result"][11]["weapons"].pop()
        weapon_data["result"][3]["weapons"].append(item_temp)
        weapon_data = weapon_data["result"]
    except Exception as e:
        logger.error(e)
        await msg.reply(
        
            "获取玩家数据出错,请稍后再试!"
        )
        return False
    weapon_temp = {}
    # start_time2 = time.time()
    for item in weapon_data:
        for item2 in item["weapons"]:
            if item2["stats"]["values"] != {}:
                if item2["stats"]["values"]["kills"] != 0.0:
                    weapon_temp[zhconv.convert(item2["name"], 'zh-cn')] = [
                        int(item2["stats"]["values"]["kills"]),  # 击杀
                        "{:.2f}".format(
                            item2["stats"]["values"]["kills"] / item2["stats"]["values"]["seconds"] * 60) if
                        item2["stats"]["values"]["seconds"] != 0 else "0",  # kpm
                        "{:.2f}%".format(
                            item2["stats"]["values"]["hits"] / item2["stats"]["values"]["shots"] * 100) if
                        item2["stats"]["values"]["shots"] * 100 != 0 else "0",  # 命中率
                        "{:.2f}%".format(
                            item2["stats"]["values"]["headshots"] / item2["stats"]["values"]["kills"] * 100) if
                        item2["stats"]["values"]["kills"] != 0 else "0",  # 爆头率
                        "{:.2f}".format(item2["stats"]["values"]["hits"] / item2["stats"]["values"]["kills"]) if
                        item2["stats"]["values"]["kills"] != 0 else "0",  # 效率

                        item2["imageUrl"].replace("[BB_PREFIX]",
                                                  "https://eaassets-a.akamaihd.net/battlelog/battlebinary",
                                                  ),
                        "{:.0f}h".format(item2["stats"]["values"]["seconds"] / 3600),  # 游戏时长
                    ]
    weapon_temp_sorted = sorted(weapon_temp.items(), key=lambda x: x[1][0], reverse=True)  # 得到元组列表
    # print(weapon_temp_sorted)
    weapon_list = weapon_temp_sorted[:4]
    weapon1 = []
    weapon2 = []
    weapon3 = []
    weapon4 = []
    weapon123 = [weapon1, weapon2, weapon3, weapon4]
    i = 0
    # noinspection PyBroadException
    try:
        while i <= 1:
            weapon_item = weapon123[i]
            weapon_item.append(weapon_list[i][0])
            weapon_item.append(weapon_list[i][1][0])
            weapon_item.append(weapon_list[i][1][1])
            weapon_item.append(weapon_list[i][1][2])
            weapon_item.append(weapon_list[i][1][3])
            weapon_item.append(weapon_list[i][1][4])
            weapon_item.append(weapon_list[i][1][5])
            weapon_item.append(weapon_list[i][1][6])
            i += 1
    except Exception as e:
        logger.error(e)
        await msg.reply(
        
            "数据不足!"
        )
        return False
    weapon_data = weapon1

    # 载具数据
    # noinspection PyBroadException
    try:
        # noinspection PyBroadException
        try:
            # vehicle_data = await InfoCache(str(player_pid), "vehicle").get_data()
            vehicle_data = scrape_index_tasks[2].result()
        except Exception as e:
            logger.error(e)
            await InfoCache(str(player_pid), "vehicle").update_cache()
            vehicle_data = await InfoCache(str(player_pid), "vehicle").get_data()
        vehicle_data = vehicle_data["result"]
    except Exception as e:
        logger.error(e)
        await msg.reply(
        
            "获取玩家数据出错,请稍后再试!"
        )
        return False
    vehicle_temp = {}
    for item1 in vehicle_data:
        for item2 in item1["vehicles"]:
            vehicle_temp[zhconv.convert(item2["name"], 'zh-cn')] = [
                int(item2["stats"]["values"]["kills"]),  # 击杀
                "{:.2f}".format(item2["stats"]["values"]["kills"] / item2["stats"]["values"]["seconds"] * 60)
                if item2["stats"]["values"]["seconds"] != 0 else "0",
                # kpm
                int(item2["stats"]["values"]["destroyed"]),  # 摧毁
                "{:.2f}h".format(item2["stats"]["values"]["seconds"] / 3600),  # 时长
                item2["imageUrl"].replace("[BB_PREFIX]", "https://eaassets-a.akamaihd.net/battlelog/battlebinary")
                # 图片url
            ]
    vehicle_temp_sorted = sorted(vehicle_temp.items(), key=lambda x: x[1][0], reverse=True)  # 得到元组列表
    # print(weapon_temp_sorted)
    vehicle_list = vehicle_temp_sorted[:4]
    vehicle1 = []
    vehicle2 = []
    vehicle3 = []
    vehicle4 = []
    vehicle123 = [vehicle1, vehicle2, vehicle3, vehicle4]
    i = 0
    while i <= 1:
        vehicle_temp = vehicle123[i]
        vehicle_temp.append(vehicle_list[i][0])
        vehicle_temp.append(vehicle_list[i][1][0])
        vehicle_temp.append(vehicle_list[i][1][1])
        vehicle_temp.append(vehicle_list[i][1][2])
        vehicle_temp.append(vehicle_list[i][1][3])
        vehicle_temp.append(vehicle_list[i][1][4])
        i += 1
    vehicle_data = vehicle1

    # 制作图片
    # 背景图
    # 底图选择
    # bg_img = Image.open(await pic_custom(player_pid))
    bg_img = Image.open(bg_pic.choose_bg(player_pid, "stat"))
    width, height = bg_img.size
    if not (width == 1080 and height == 2729):
        b1 = width / 1080
        b2 = height / 2729
        if b1 < 1 or b2 < 1:
            倍数 = 1 / b1 if 1 / b1 > 1 / b2 else 1 / b2
        else:
            倍数 = b1 if b1 < b2 else b2
        # 放大图片
        bg_img = bg_img.resize((int(width * 倍数) + 1, int(height * 倍数) + 1), Image.ANTIALIAS)
        # 裁剪到中心位置
        width, height = bg_img.size
        left = (width - 1080) / 2
        top = (height - 2729) / 2
        right = (width + 1080) / 2
        bottom = (height + 2729) / 2
        bg_img = bg_img.crop((left, top, right, bottom))
        底图 = Image.open(f"app/data/battlefield/pic/bg/底图2.png").convert('RGBA')
        bg_img.paste(底图, (0, 0), 底图)
    draw = ImageDraw.Draw(bg_img)
    # 字体路径
    font_path = 'app/data/battlefield/font/BFText-Regular-SC-19cf572c.ttf'
    # 设定字体
    title_font = ImageFont.truetype(font_path, 50)
    star_font = ImageFont.truetype(font_path, 45)
    time_font = ImageFont.truetype(font_path, 25)
    name_font = ImageFont.truetype(font_path, 45)
    content_font = ImageFont.truetype(font_path, 40)
    # 等级字体
    rank_font = ImageFont.truetype(r'C:\Windows\Fonts\simhei.TTF', 80)
    SavePic = "app/data/battlefield/Temp/" + str(int(time.time())) + ".png"
    # 玩家头像获取
    player_img = await playerPicDownload(html["avatar"], html["userName"])
    # 玩家头像打开
    avatar_img = Image.open(player_img).convert('RGBA')
    # 玩家头像拼接
    bg_img.paste(avatar_img, (64, 91))
    # 玩家ID拼接
    draw.text((300, 225), "ID:%s" % html["userName"], fill='white', font=title_font)
    # 时间拼接
    time_now = time.strftime("%Y/%m/%d-%H:%M", time.localtime(time.time()))
    draw.text((790, 260), time_now, fill='white', font=time_font)
    # 第一个黑框
    # 等级
    if int(data_list[2]) >= 100:
        draw.text((173, 370), data_list[2], fill='white', font=rank_font)
    elif int(data_list[2]) >= 10:
        draw.text((195, 370), data_list[2], fill='white', font=rank_font)
    else:
        draw.text((215, 370), data_list[2], fill='white', font=rank_font)
    # 游戏时长
    draw.text((410, 385), '游戏时长:%.1f小时' % data_list[14], fill='white', font=name_font)
    # 击杀
    draw.text((210, 510), f'击杀:{data_list[6]}', fill='white', font=content_font)
    # 死亡
    draw.text((210, 560), f'死亡:{data_list[7]}', fill='white', font=content_font)
    # kd
    draw.text((213, 610), f'KD:{data_list[4]}', fill='white', font=content_font)
    # 胜局
    draw.text((600, 510), f'胜局:{data_list[17]}', fill='white', font=content_font)
    # 败局
    draw.text((600, 560), f'败局:{data_list[18]}', fill='white', font=content_font)
    # 胜率
    draw.text((600, 610), f'胜率:{data_list[10]}', fill='white', font=content_font)
    # 第二个黑框
    # 兵种
    # 兵种图片打开
    class_img = Image.open('app/data/battlefield/pic/classes/%s.png' % data_list[19]).convert('RGBA')
    # 兵种图片拉伸
    class_img = class_img.resize((90, 90), Image.ANTIALIAS)
    # 兵种图片拼接
    bg_img.paste(class_img, (192, 735), class_img)
    # 最佳兵种
    class_dict = {"Assault": "突击兵", "Cavalry": "骑兵", "Medic": "医疗兵",
                  "Pilot": "飞行员", "Scout": "侦察兵", "Support": "支援兵", "Tanker": "坦克手"}
    best_class = class_dict[data_list[19]]
    draw.text((450, 760), f'最佳兵种:{best_class}', fill='white', font=name_font)
    # 协助击杀
    draw.text((210, 890), f'协助击杀:{int(data_list[20])}', fill='white', font=content_font)
    # 复活数
    draw.text((210, 940), f'复活数:{int(data_list[21])}', fill='white', font=content_font)
    # 修理数
    draw.text((210, 990), f'修理数:{int(data_list[22])}', fill='white', font=content_font)
    # 最多连杀
    draw.text((600, 890), f'最高连杀:{int(data_list[23])}', fill='white', font=content_font)
    # 治疗数
    draw.text((600, 940), f'治疗数:{int(data_list[24])}', fill='white', font=content_font)
    # 狗牌数
    draw.text((600, 990), f'狗牌数:{int(data_list[25])}', fill='white', font=content_font)

    # 是否联ban

    if bfban_status != "未查询到联ban信息":
        draw.text((430, 1130), f'联ban信息:{bfban_status}', fill='white', font=name_font)
    else:
        draw.text((417, 1130), f'{bfban_status}', fill='white', font=name_font)

    # KPM
    draw.text((213, 1260), f'KPM:{data_list[9]}', fill='white', font=content_font)
    # 步战KD
    draw.text((210, 1310), f'步战KD:{data_list[5]}', fill='white', font=content_font)
    # 命中率
    draw.text((210, 1360), '命中率:%.2f%%' % data_list[11], fill='white', font=content_font)
    # 最远爆头距离
    draw.text((210, 1410), f'最远爆头距离:{data_list[13]}米', fill='white', font=content_font)
    # SPM
    draw.text((600, 1260), f'SPM:{data_list[8]}', fill='white', font=content_font)
    # 技巧值
    draw.text((600, 1310), f'技巧值:{data_list[3]}', fill='white', font=content_font)
    # 爆头率
    draw.text((600, 1360), f'爆头率:{data_list[12]}', fill='white', font=content_font)
    # bg_img.show()
    # range(4) 0 - 3
    # 最佳武器
    i = 2
    if i == 2:
        # 间距 623
        # 武器图片获取
        pic_url = await PicDownload(weapon_data[6])
        # 打开武器图像
        weapon_png = Image.open(pic_url).convert('RGBA')
        # 拉伸
        weapon_png = weapon_png.resize((588, 147))
        star = str(int(weapon_data[1] / 100))
        weapons_star = "★"
        # tx_img = Image.open("")
        if weapon_data[1] >= 10000:
            # 金色
            tx_img = Image.open("app/data/battlefield/pic/tx/" + "1.png").convert(
                'RGBA')
            tx_img = tx_img.resize((267, 410))
            bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
            draw.text((179, 506 + i * 580), weapons_star, font=star_font, fill=(255, 132, 0))
            draw.text((233, 509 + i * 580), star, font=star_font, fill=(255, 132, 0))
        elif 6000 <= weapon_data[1] < 10000:
            # 蓝色
            tx_img = Image.open("app/data/battlefield/pic/tx/" + "2.png").convert(
                'RGBA')
            tx_img = tx_img.resize((267, 410))
            bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
            draw.text((179, 506 + i * 580), weapons_star, font=star_font, fill=(74, 151, 255))
            draw.text((233, 509 + i * 580), star, font=star_font, fill=(74, 151, 255))
        elif 4000 <= weapon_data[1] < 6000:
            # 白色
            tx_img = Image.open("app/data/battlefield/pic/tx/" + "3.png").convert(
                'RGBA')
            tx_img = tx_img.resize((267, 410))
            bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
            draw.text((179, 506 + i * 580), weapons_star, font=star_font)
            draw.text((233, 509 + i * 580), star, font=star_font)
        elif 0 <= weapon_data[1] < 4000:
            draw.text((179, 506 + i * 580), weapons_star, font=star_font)
            draw.text((233, 509 + i * 580), star, font=star_font)
        # 武器图像拼接
        bg_img.paste(weapon_png, (250, 392 + i * 580), weapon_png)
        draw.text((210, 630 + i * 580), weapon_data[0], font=name_font)
        draw.text((210, 730 + i * 580), "击杀:%d" % weapon_data[1], font=content_font)
        draw.text((600, 730 + i * 580), f"kpm:{weapon_data[2]}", font=content_font)
        draw.text((210, 780 + i * 580), "命中率:%s" % weapon_data[3], font=content_font)
        draw.text((600, 780 + i * 580), "爆头率:%s" % weapon_data[4], font=content_font)
        draw.text((210, 830 + i * 580), "效率:%s" % weapon_data[5], font=content_font)
        draw.text((600, 830 + i * 580), "时长:%s" % weapon_data[7], font=content_font)
    # 最佳载具
    i = 3
    if i == 3:
        # 间距 623
        # 武器图片获取
        pic_url = await PicDownload(vehicle_data[5])
        # 打开武器图像
        weapon_png = Image.open(pic_url).convert('RGBA')
        # 拉伸
        weapon_png = weapon_png.resize((563, 140))
        # 星星数
        star = str(int(vehicle_data[1] / 100))
        weapons_star = "★"
        # tx_img = Image.open("")
        if vehicle_data[1] >= 10000:
            # 金色
            tx_img = Image.open("app/data/battlefield/pic/tx/" + "1.png").convert(
                'RGBA')
            tx_img = tx_img.resize((267, 410))
            bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
            draw.text((179, 506 + i * 580), weapons_star, font=star_font, fill=(255, 132, 0))
            draw.text((233, 509 + i * 580), star, font=star_font, fill=(255, 132, 0))
        elif 6000 <= vehicle_data[1] < 10000:
            # 蓝色
            tx_img = Image.open("app/data/battlefield/pic/tx/" + "2.png").convert(
                'RGBA')
            tx_img = tx_img.resize((267, 410))
            bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
            draw.text((179, 506 + i * 580), weapons_star, font=star_font, fill=(74, 151, 255))
            draw.text((233, 509 + i * 580), star, font=star_font, fill=(74, 151, 255))
        elif 4000 <= vehicle_data[1] < 6000:
            # 白色
            tx_img = Image.open("app/data/battlefield/pic/tx/" + "3.png").convert(
                'RGBA')
            tx_img = tx_img.resize((267, 410))
            bg_img.paste(tx_img, (420, 290 + i * 580), tx_img)
            draw.text((179, 506 + i * 580), weapons_star, font=star_font)
            draw.text((233, 509 + i * 580), star, font=star_font)
        elif 0 <= vehicle_data[1] < 4000:
            draw.text((179, 506 + i * 580), weapons_star, font=star_font)
            draw.text((233, 509 + i * 580), star, font=star_font)
        # 武器图像拼接
        bg_img.paste(weapon_png, (250, 392 + i * 580), weapon_png)
        draw.text((210, 630 + i * 580), vehicle_data[0], font=name_font)
        draw.text((210, 730 + i * 580), "击杀:%d" % vehicle_data[1], font=content_font)
        draw.text((600, 730 + i * 580), f"kpm:{vehicle_data[2]}", font=content_font)
        draw.text((210, 780 + i * 580), "摧毁:%s" % vehicle_data[3], font=content_font)
        draw.text((600, 780 + i * 580), f"时长:{vehicle_data[4]}", font=content_font)
    bg_img = bg_img.convert('RGB')
    if if_cheat:
        bg_img = bg_img.convert('L')
    end_time = time.time()
    logger.info(f"接口+制图耗时:{end_time - start_time}秒")
    start_time4 = time.time()
    if not if_cheat:
        img = bg_img #pil合成的对象
        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        imgByte = io.BytesIO(imgByteArr.getvalue())
        img_url = await bot.client.create_asset(imgByte)
        await msg.reply(img_url,type=MessageTypes.IMG)
    else:
        img = bg_img #pil合成的对象
        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        imgByte = io.BytesIO(imgByteArr.getvalue())
        img_url = await bot.client.create_asset(imgByte)
        await msg.reply(img_url,type=MessageTypes.IMG)
        await msg.reply(f"案件地址:{bf_url}")
    end_time4 = time.time()
    if end_time4 - start_time4 > 60:
        await msg.reply(
            f"发送耗时:{int(end_time4 - start_time4)}秒,似乎被限制了呢= ="
        )
    logger.info(f"发送耗时:{end_time4 - start_time4}秒")
    record.player_stat_counter(msg.author_id, str(player_pid), str(player_name))
# TODO 5:最近
@bot.command(name='recent')
async def recent(msg:Message, player_name: str=None):
    if player_name!=None:
        # noinspection PyBroadException
        try:
            player_info = await getPid_byName(player_name)
        except Exception as e:
            logger.error(e)
            await msg.reply(
                f"网络出错，请稍后再试!"
            )
            return False
        if player_info['personas'] == {}:
            await msg.reply(
                f"玩家[{player_name}]不存在"
            )
            return False
        else:
            player_pid = player_info['personas']['persona'][0]['personaId']
            player_name = player_info['personas']['persona'][0]['displayName']
    else:
        # 检查绑定没有,没有绑定则终止，绑定了就读缓存的pid
        if not record.check_bind(msg.author_id):
            await msg.reply(
                f"请先使用'/绑定+你的游戏名字'进行绑定\n例如:/绑定 xxx"
            )
            return False
        else:
            # noinspection PyBroadException
            try:
                player_pid = record.get_bind_pid(msg.author_id)
                player_name = record.get_bind_name(msg.author_id)
            except Exception as e:
                logger.error(e)
                await msg.reply(
                    "绑定信息过期,请重新绑定!"
                )
                return
    await msg.reply(
        "查询ing"
    )
    # 组合网页地址
    try:
        start_time = time.time()
        url = "https://battlefieldtracker.com/bf1/profile/pc/" + player_name
        head_temp = {
            "Connection": "keep-alive",
        }
        # async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=head_temp, timeout=10)
        end_time = time.time()
        html = response.text
        # 处理网页超时
        if html == "timed out":
            raise Exception
        elif html == {}:
            raise Exception

        soup = BeautifulSoup(html, "html.parser")  # 查找符合要求的字符串 形成列表
        for item in soup.find_all("div", class_="card-body player-sessions"):
            # 输出检查
            # print(item)
            # 转换成字符串用正则来挑选数据
            item = str(item)
            data_list = []
            # 只要前3组数据
            i = 0
            c = 0
            re_time = re.compile(r'<span data-livestamp="(.*?).000Z"></span></h4>')
            re_spm = re.compile(r'<div>(.*?)</div>')
            re_kd = re.compile(r'<div>(.*?)</div>')
            re_kpm = re.compile(r'<div>(.*?)</div>')
            re_time_play = re.compile(r'<div>(.*?)</div>')
            count = len(re.findall(re_spm, item)) / 6
            while i < count and i < 3:
                data = ["", "", "", "", "", "", ""]
                time_point = re.findall(re_time, item)[0 + i]
                time_point = time_point.replace("T", " ")
                spm = re.findall(re_spm, item)[0 + c]
                kd = re.findall(re_kd, item)[1 + c]
                kpm = re.findall(re_kpm, item)[2 + c]
                time_play = re.findall(re_time_play, item)[5 + c]
                data[1] = time_point + "\n"
                data[2] = "SPM:" + spm + "\n"
                data[3] = "KD:" + kd + "\n"
                data[4] = "KPM" + kpm + "\n"
                data[5] = "游玩时长:" + time_play + "\n"
                data[6] = "=" * 11 + "\n"
                data_list.append(data)
                i += 1
                c += 6
            data_list[-1][-1] = data_list[-1][-1].replace("\n", "")
            data_list_str= " "
            for k in data_list:
                    list_str="".join(n for n in k)
                    data_list_str=data_list_str+list_str
            await msg.reply(
                data_list_str
            )
            record.recent_counter(msg.author_id, str(player_pid), str(player_name))
            logger.info(f'查询最近耗时:{end_time - start_time}')
            return True
        await msg.reply(
            "没有查询到最近记录哦~"
        )
        return
    except Exception as e:
        logger.warning(e)
        await msg.reply(
            "网络出错，请稍后再试!"
        )
# TODO 6:对局
@bot.command(name='matches',aliases=['最近'])
async def matches(msg:Message, player_name: str=None):
    if player_name!=None:
        try:
            player_info = await getPid_byName(player_name)
        except Exception as e:
            logger.error(e)
            await msg.reply(
                f"网络出错，请稍后再试!"
            )
            return False
        if player_info['personas'] == {}:
            await msg.reply(
                f"玩家[{player_name}]不存在"
            )
            return False
        else:
            player_pid = player_info['personas']['persona'][0]['personaId']
            player_name = player_info['personas']['persona'][0]['displayName']
    else:
        # 检查绑定没有,没有绑定则终止，绑定了就读缓存的pid
        if not record.check_bind(msg.author_id):
            await msg.reply(
                f"请先使用'/绑定+你的游戏名字'进行绑定\n例如:/绑定 xxx"
            )
            return False
        else:
            # noinspection PyBroadException
            try:
                player_pid = record.get_bind_pid(msg.author_id)
                player_name = record.get_bind_name(msg.author_id)
            except Exception as e:
                logger.error(e)
                await msg.reply(
                    "绑定信息过期,请重新绑定!"
                )
                return
    await msg.reply(
        "查询ing"
    )
    # 获取数据
    start_time = time.time()
    player_data = []
    # noinspection PyBroadException
    try:
        url1 = 'https://battlefieldtracker.com/bf1/profile/pc/' + player_name + '/matches'
        header = {
            "Connection": "keep-alive"
        }
        # async with httpx.AsyncClient() as client:
        response = await client.get(url1, headers=header, timeout=5)
    except Exception as e:
        logger.warning(e)
        await msg.reply(
            "网络出错,请稍后再试!"
        )
        return False

    end_time = time.time()
    logger.info(f"获取对局列表耗时:{end_time - start_time}")
    html1 = response.text
    # 处理网页超时
    if html1 == "timed out":
        raise Exception
    elif html1 == {}:
        raise Exception
    elif html1 == 404:
        raise Exception
    soup = BeautifulSoup(html1, "html.parser")  # 查找符合要求的字符串 形成列表
    matches_list = []
    # for i in soup.find_all("p", class_="description"):
    #     player_data.append("".join(re.findall(re.compile(r'<p class="description">(.*?)</p>'), str(i))))
    # player_data = player_data[:3]
    header = {
        "Connection": "keep-alive"
    }
    for item in soup.find_all("div", class_="card matches"):
        matches_list = re.findall(re.compile(r'href="(.*?)"'), str(item))[:3]  # 前几个对局数据
    if len(matches_list) == 0:
        await msg.reply(
            '查询失败'
        )
        return False
    start_time2 = time.time()
    scrape_index_tasks = []
    # noinspection PyBroadException
    try:
        # 并发前n个地址，并获取其中的数据
        # async with httpx.AsyncClient(headers=header) as client:
        for item2 in matches_list:
            url_temp = 'https://battlefieldtracker.com' + item2
            scrape_index_tasks.append(asyncio.ensure_future(client.get(url_temp, headers=header, timeout=10)))
        await asyncio.gather(*scrape_index_tasks)
    except Exception as e:
        logger.error(e)
        await msg.reply(
            "网络出错，请稍后再试!"
        )
        return False
    end_time2 = time.time()
    logger.info(f"对局耗时:{end_time2 - start_time2}")
    start_time3 = time.time()
    for result in scrape_index_tasks:
        response = result.result()
        html2 = response.text
        if html2 == "timed out":
            raise Exception
        elif html2 == 404:
            raise Exception
        soup = BeautifulSoup(html2, "html.parser")
        for item in soup.find_all("div", class_="activity-details"):
            # 日期
            player_data.append(
                "游玩日期:" + re.findall(re.compile(r'<span class="date">(.*?)</span>'), str(item))[0] + '\n')
            # 服务器名字
            player_data.append(
                "服务器:" +
                re.findall(re.compile(r'<small class="hidden-sm hidden-xs">(.*?)</small></h2>'), str(item))[0][:20]
                + '\n'
            )
            # 模式名
            player_data.append(re.findall(re.compile(r'<span class="type">(.*?)</span>'), str(item))[0]
                               .replace("BreakthroughLarge0", "行动模式").replace("Frontlines", "前线")
                               .replace("Domination", "抢攻").replace("Team Deathmatch", "团队死斗")
                               .replace("War Pigeons", "战争信鸽").replace("Conquest", "征服")
                               .replace("AirAssault0", "空中突袭").replace("Rush", "突袭")
                               .replace("Breakthrough", "闪击行动") + '-')
            # 地图名
            player_data.append(
                re.findall(re.compile(r'<h2 class="map-name">(.*?)<small class="hidden-sm hidden-xs">'), str(item))[0]
                .replace("Galicia", "加利西亚").replace("Giant's Shadow", "庞然闇影").replace("Brusilov Keep", "勃鲁西洛夫关口")
                .replace("Rupture", "决裂").replace("Soissons", "苏瓦松").replace("Amiens", "亚眠")
                .replace("St. Quentin Scar", "圣康坦的伤痕").replace("Argonne Forest", "阿尔贡森林")
                .replace("Ballroom Blitz", "宴厅").replace("MP_Harbor", "泽布吕赫").replace("River Somme", "索姆河")
                .replace("Prise de Tahure", "攻占托尔").replace("Fao Fortress", "法欧堡").replace("Achi Baba", "2788")
                .replace("Cape Helles", "海丽丝峡").replace("Tsaritsyn", "察里津").replace("Volga River", "窝瓦河")
                .replace("Empire's Edge", "帝国边境").replace("ŁUPKÓW PASS", "武普库夫山口")
                .replace("Verdun Heights", "凡尔登高地").replace("Fort De Vaux", "垃圾厂")
                .replace("Sinai Desert", "西奈沙漠").replace("Monte Grappa", "拉粑粑山").replace("Suez", "苏伊士")
                .replace("Albion", "阿尔比恩").replace("Caporetto", "卡波雷托").replace("Passchendaele", "帕斯尚尔")
                .replace("Nivelle Nights", "尼维尔之夜").replace("MP_Naval", "黑尔戈兰湾").replace("", "")
                + '\n')
        # 此时player_data已有服务器名字 游玩的时间 模式-地图名字
        # 玩家对局数据
        for item2 in soup.find_all("div", class_="player active"):
            soup2 = item2
            Time_data = 0
            score_data = []
            for i2 in soup2.find_all("div", class_="quick-stats"):
                # 数组 分别是得分 击杀 死亡 协助 K/D
                # name_data = re.findall(re.compile(r'<div class="name">(.*?)</div>'), str(i2))
                score_data = re.findall(re.compile(r'<div class="value">(.*?)</div>'), str(i2))
                Time_data = re.findall(re.compile(r'<span class="player-subline">([\s\S]*?)</span>'), str(item2))[0] \
                    .replace("\r", "").replace("\n", "").replace("Played for ", "").replace(" ", "")
                # 时间
            # 转换成秒数

            # noinspection PyBroadException
            try:
                Time_data_int = int(Time_data[:Time_data.find("m")]) * 60 + int(
                    Time_data[Time_data.find("m") + 1:Time_data.find("s")])
            except Exception as e:
                logger.warning(e)
                Time_data_int = 1
            # 得分
            Score_data = score_data[0]

            # SPM
            # noinspection PyBroadException
            try:
                Spm_data = int(Score_data.replace(",", "")) / int(Time_data_int / 60)
            except Exception as e:
                logger.warning(e)
                Spm_data = 0
            # 击杀
            Kill_data = score_data[1]

            # KPM
            # noinspection PyBroadException
            try:
                Kpm_data = int(Kill_data) / int(Time_data_int / 60)
            except Exception as e:
                logger.warning(e)
                Kpm_data = 0
            # 死亡数
            Death_data = score_data[2]
            # KD
            KD_data = score_data[4]
            if KD_data != '-':
                KD_data = int(Kill_data) / int(Death_data) if int(Death_data) != 0 else 1
            player_data.append(f'击杀:{Kill_data}\t')
            player_data.append(f'死亡:{Death_data}\n')
            if KD_data != '-':
                player_data.append('KD:%.2f\t' % KD_data)
            else:
                player_data.append(f'KD:{KD_data}\t')
            player_data.append(f'得分:{Score_data}\n')
            player_data.append(f'KPM:{Kpm_data:.2f}\t')
            player_data.append(f'SPM:{Spm_data:.2f}\n')
            player_data.append(f'游玩时长:{int(Time_data_int / 60)}分{Time_data_int % 60}秒\n')
            player_data.append("=" * 20 + "\n")
    # noinspection PyBroadException
    try:
        player_data[-1] = player_data[-1].replace("\n", '')
    except Exception as e:
        logger.error(e)
        await msg.reply(
            f"对局数据为空QAQ"
        )
        return
    end_time3 = time.time()
    logger.info(f"解析对局数据耗时:{end_time3 - start_time3}")
    player_data[-1] = player_data[-1].replace("\n", "")
    player_data_str=" ".join(n for n in player_data)    
    await msg.reply(
        player_data_str
    )
    record.matches_counter(msg.author_id, str(player_pid), str(player_name))
    return True


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
# TODO:天眼查
@bot.command(name='player_tyc',aliases=['天眼查'])
async def player_tyc(msg:Message,player_name: str=None):
    if player_name!=None:
        try:
            player_info = await getPid_byName(player_name)
        except Exception as e:
            logger.error(e)
            await msg.reply(
                f"网络出错，请稍后再试"
            )
            return False
        if player_info['personas'] == {}:
            await msg.reply(
                f"玩家[{player_name}]不存在"
            )
            return False
        else:
            player_pid = player_info['personas']['persona'][0]['personaId']
            player_name = player_info['personas']['persona'][0]['displayName']
    else:
        # 检查绑定没有,没有绑定则终止，绑定了就读缓存的pid
        if not record.check_bind(msg.author_id):
            await msg.reply(
                f"请先使用'-绑定+你的游戏名字'进行绑定\n例如:-绑定shlsan13"
            )
            return False
        else:
            # noinspection PyBroadException
            try:
                player_pid = record.get_bind_pid(msg.author_id)
                player_name = record.get_bind_name(msg.author_id)
            except Exception as e:
                logger.error(e)
                await msg.reply(
                
                    "绑定信息过期,请重新绑定!"
                )
                return
    await msg.reply(
        "查询ing"
    )

    data_list = ["=" * 20 + '\n', '玩家姓名:%s\n' % player_name, '玩家ID:%s\n' % player_pid, "=" * 20 + '\n', ]

    scrape_index_tasks = [
        asyncio.ensure_future(get_player_recentServers(player_pid)),
        asyncio.ensure_future(tyc_waterGod_api(player_pid)),
        asyncio.ensure_future(tyc_record_api(player_pid)),
        asyncio.ensure_future(tyc_bfban_api(player_pid)),
        asyncio.ensure_future(tyc_bfeac_api(player_name)),
        asyncio.ensure_future(server_playing(player_pid)),
        asyncio.ensure_future(tyc_check_vban(player_pid)),
    ]
    tasks = asyncio.gather(*scrape_index_tasks)
    try:
        await tasks
    except Exception as e:
        logger.error(e)
        await msg.reply(
            f"网络出错,请稍后再试!"
        )
        return False
    try:
        recent_play_list = scrape_index_tasks[0].result()
        if type(recent_play_list) == dict:
            data_list.append("最近游玩:\n")
            i = 0
            if len(recent_play_list["result"]) >= 3:
                while i <= 2:
                    data_list.append(recent_play_list["result"][i]["name"][:25] + "\n")
                    i += 1
            else:
                for item in recent_play_list["result"]:
                    data_list.append(item["name"][:25] + "\n")
            data_list.append("=" * 20 + '\n')
    except Exception as e:
        msg.reply(f"获取最近游玩出错:{e}")
        pass
    try:
        # vban检查
        vban_info = scrape_index_tasks[6].result()
        vban_num = None
        if type(vban_info) == str:
            pass
        else:
            vban_num = len(vban_info["vban"])
        html1 = scrape_index_tasks[1].result().text
        if html1 == 404:
            raise Exception
        html1 = eval(html1)
        if html1["status"]:
            player_server = len(html1["result"][0]["data"])
            player_admin = len(html1["result"][1]["data"])
            player_vip = len(html1["result"][2]["data"])
            player_ban = len(html1["result"][3]["data"])
            data_list.append("拥有服务器数:%s\n" % player_server)
            data_list.append("管理服务器数:%s\n" % player_admin)
            data_list.append("服务器封禁数:%s\n" % player_ban)
            if vban_num is not None:
                data_list.append(f"VBAN数:{vban_num}\n")
            data_list.append("VIP数:%s\n" % player_vip)
            data_list.append("详细情况:https://bf.s-wg.net/#/player?pid=%s\n" % player_pid)
            data_list.append("=" * 20 + '\n')
    except Exception as e:
        logger.error(f"获取水神api出错:{e}")
        pass
    data_list_str=" ".join(n for n in data_list)
    await msg.reply(data_list_str)
@bot.command(name='bf_status',aliases=['bfstatus','bfs'])
async def bf_status(msg:Message):
    url = "https://api.gametools.network/bf1/status/?platform=pc"
    head = {
        "Connection": "Keep-Alive"
    }
    # noinspection PyBroadException
    try:
        # async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=head, timeout=5)
    except Exception as e:
        logger.error(e)
        await msg.reply(
            f"网络超时,请稍后再试!"
        )
        return False
    html = eval(response.text)
    if 'errors' in html:
        # {'errors': ['Error connecting to the database']}
        await msg.reply(
            f"{html['errors'][0]}"
        )
        return
    data1 = html["regions"][0]
    try:
        data_list1=[]
        data_list1.append(data1["modes"]["Conquest"])
        data_list1.append(data1["modes"]["BreakthroughLarge"])
        data_list1.append(data1["modes"]["TugOfWar"])
        data_list1.append(data1["modes"]["Breakthrough"])
        data_list1.append(data1["modes"]["Rush"])
        data_list1.append(data1["modes"]["Domination"])
        data_list1.append(data1["modes"]["TeamDeathMatch"])
        data_list1.append(data1["modes"]["Possession"])
        data_list1.append( data1["modes"]["AirAssault"])
        data_list1.append(data1["modes"]["ZoneControl"])
    except Exception as e:
        logger.error(f"信息获取不全{e}")
    data2 = data1
    try:
        data_list2 = []
        data_list2.append(data2["amounts"]["soldierAmount"])
        data_list2.append(data2["amounts"]["serverAmount"])
        data_list2.append(data2["amounts"]["queueAmount"])
        data_list2.append(data2["amounts"]["spectatorAmount"])
        data_list2.append(data2["amounts"]["communityServerAmount"])
        data_list2.append(data2["amounts"]["communitySoldierAmount"])
        data_list2.append(data2["amounts"]["communityQueueAmount"])
        data_list2.append(data2["amounts"]["communitySpectatorAmount"])
        data_list2.append(data2["amounts"]["diceServerAmount"])
        data_list2.append(data2["amounts"]["diceSoldierAmount"])
        data_list2.append(data2["amounts"]["diceQueueAmount"])
        data_list2.append(data2["amounts"]["diceSpectatorAmount"])
    except Exception as e:
        logger.error(f"信息获取不全{e}")
    try:
        s1="当前在线:%d" % data_list2[0] + "\n"
    except:
        s1=""
    try:
        s2="服务器数:%d" % data_list2[1] + "\n"
    except:
        s2=""
    try:
        s3="排队总数:%d" % data_list2[2] + "\n"
    except:
        s3=""
    try:
        s4="观众总数:%d" % data_list2[3] + "\n"
    except:
        s4=""
    s5="=" * 13+ "\n"+"私服(官服):\n"
    try:
        s6=f"服务器:{int(data_list2[4])}({int(data_list2[8])})\n"
    except:
        s6=""
    try:
        s7=f"人数:{int(data_list2[5])}({int(data_list2[9])})\n"
    except:
        s7=""
    try:
        s8=f"排队:{int(data_list2[6])}({int(data_list2[10])})\n"
    except:
        s8=""
    try:
        s9=f"观众:{int(data_list2[7])}({int(data_list2[11])})\n"
    except:
        s9=""
    s10="=" * 13+ "\n"
    try:
        s11="征服:%d" % data_list1[0] + "\t"
    except:
        s11=""
    try:
        s12="行动:%d" % data_list1[1] + "\n"
    except:
        s12=""
    try:
        s13="前线:%d" % data_list1[2] + "\t"
    except:
        s13=""
    try:
        s14="突袭:%d" % data_list1[4] + "\n"
    except:
        s14=""
    try:
        s15="抢攻:%d" % data_list1[5] + "\t"
    except:
        s15=""
    try:
        s16="闪击行动:%d" % data_list1[3] + "\n"
    except:
        s16=""
    try:
        s17="团队死斗:%d" % data_list1[6] + "\t"
    except:
        s17=""
    try:
        s18="战争信鸽:%d" % data_list1[7] + "\n"
    except:
        s18=""
    try:
        s19="空中突袭:%d" % data_list1[8] + "\t"   
    except:
        s19=""
    try:     
        s20="空降补给:%d" % data_list1[9] + "\n"
    except:
        s20=""
    strs=s1+s2+s3+s4+s5+s6+s7+s8+s9+s10+s11+s12+s13+s14+s15+s16+s17+s18+s19+s20
    await msg.reply(
        # "----亚服信息----\n",
        # "=" * 13, "\n",
        strs
    )
# TODO: 查询统计
@bot.command(name='bf_checkCounter',aliases=['查询统计','统计'])
async def bf_checkCounter(msg:Message):
    if not record.check_bind(msg.author_id):
        await msg.reply(
            f"没有找到你的信息!\n请先使用'-绑定+你的游戏名字'进行绑定\n例如:-绑定shlsan13"
        )
        return False
    try:
        player_pid = record.get_bind_pid(msg.author_id)
        player_name = record.get_bind_name(msg.author_id)
    except Exception as e:
        logger.error(e)
        await msg.reply(
            "绑定信息出错,请重新绑定!"
        )
        return
    bind_info = record.get_bind_counter(msg.author_id)
    weapon_info = record.get_weapon_counter(msg.author_id)
    vehicle_info = record.get_vehicle_counter(msg.author_id)
    stat_info = record.get_stat_counter(msg.author_id)
    recent_info = record.get_recent_counter(msg.author_id)
    matches_info = record.get_matches_counter(msg.author_id)
    tyc_info = None
    report_info = None
    # noinspection PyBroadException
    try:
        tyc_info = record.get_tyc_counter(msg.author_id)
        report_info = record.get_report_counter(msg.author_id)
    except Exception as e:
        logger.warning(e)
        pass
    try:
        strs=f"你的信息如下:\n"+f"Id:{player_name}\n"+f"Pid:{player_pid}\n"+f"绑定次数:{len(bind_info)}\n"+f"查询武器次数:{len(weapon_info)}\n"+f"查询载具次数:{len(vehicle_info)}\n"+f"查询生涯次数:{len(stat_info)}\n"+f"查询最近次数:{len(recent_info)}\n"+f"查询对局次数:{len(matches_info)}"
    except Exception as e:
        logger.error(e)
    await msg.reply(
        strs
    )
# TODO 战役信息
@bot.command(name='op_info',aliases=['行动','战役','op'])
async def op_info(msg:Message):
    global bf_aip_header, bf_aip_url
    session = record.get_session()
    bf_aip_header["X-Gatewaysession"] = session
    body = {
        "jsonrpc": "2.0",
        "method": "CampaignOperations.getPlayerCampaignStatus",
        "params": {
            "game": "tunguska"
        },
        "id": await get_a_uuid()
    }
    # noinspection PyBroadException
    try:
        # async with httpx.AsyncClient() as client:
        response = await client.post(bf_aip_url, headers=bf_aip_header, data=json.dumps(body), timeout=5)
    except Exception as e:
        logger.error(e)
        await msg.reply(
            f"网络超时,请稍后再试!"
        )
        return
    # url2 = eval(response.text)['result']["firstBattlepack"]['images']
    # for key in url2:
    #     url3 = 'https://sparta-gw.battlelog.com/jsonrpc/pc/api' + url2[key].replace('[BB_PREFIX]', '')
    op_data = eval(response.text)
    if op_data["result"] == '':
        await msg.reply(
            f"当前无进行战役信息!"
        )
        return
    return_list = []
    from time import strftime, gmtime
    return_list.append(zhconv.convert(f"战役名称:{op_data['result']['name']}\n", "zh-cn"))
    # return_list.append(zhconv.convert(f'战役描述:{op_data["result"]["shortDesc"]}\n', "zh-cn"))
    return_list.append('战役地点:')
    for key in op_data["result"]:
        if key.startswith("op") and op_data["result"][key] != "":
            return_list.append(zhconv.convert(f'{op_data["result"][key]["name"]} ', "zh-cn"))
    return_list.append(strftime("\n剩余时间:%d天%H小时%M分", gmtime(op_data["result"]["minutesRemaining"] * 60)))
    return_list_str="".join(n for n in return_list)
    await msg.reply(
        return_list_str
    )
    # TODO 图片交换
@bot.command(name='Scrap_Exchange',aliases=['交换','ex'])
async def Scrap_Exchange(msg:Message):
    global bf_aip_header, bf_aip_url
    i = 0
    file_path = f'app/data/battlefield/exchange/{(date.today() + timedelta(days=i)).strftime("%#m月%#d日")}.png'
    while (not os.path.exists(file_path)) and (i >= -31):
        i -= 1
        file_path = f'app/data/battlefield/exchange/{(date.today() + timedelta(days=i)).strftime("%#m月%#d日")}.png'
    jh_time = (date.today() + timedelta(days=0)).strftime("%#m月%#d日")
    img_url = await bot.client.create_asset(f'{file_path}')
    await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
    session = record.get_session()
    bf_aip_header["X-Gatewaysession"] = session
    body = {
        "jsonrpc": "2.0",
        "method": "ScrapExchange.getOffers",
        "params": {
            "game": "tunguska",
        },
        "id": await get_a_uuid()
    }
    try:
        # async with httpx.AsyncClient() as client:
        response = await client.post(bf_aip_url, headers=bf_aip_header, data=json.dumps(body), timeout=5)
    except Exception as e:
        logger.error(e)
        return
    SE_data = eval(response.text)
    i = 0
    file_path_temp = f'app/data/battlefield/exchange/{(date.today() + timedelta(days=i)).strftime("%#m月%#d日")}.json'
    while (not os.path.exists(file_path_temp)) and (i >= -31):
        i -= 1
        file_path_temp = f'app/data/battlefield/exchange/{(date.today() + timedelta(days=i)).strftime("%#m月%#d日")}.json'
    if file_path_temp:
        with open(file_path_temp, 'r', encoding="utf-8") as file1:
            data_temp = json.load(file1)['result']
            if data_temp == SE_data["result"]:
                logger.info("交换未更新")
                return
    with open(f'app/data/battlefield/exchange/{jh_time}.json', 'w', encoding="utf-8") as file1:
        json.dump(SE_data, file1, indent=4)
    SE_data_list = SE_data["result"]["items"]
    # 创建一个交换物件的列表列表，元素列表的元素有价格，皮肤名字，武器名字，品质，武器图片
    SE_list = []
    for item in SE_data_list:
        temp_list = [item["price"], zhconv.convert(item["item"]["name"], 'zh-cn')]
        # 处理成简体
        temp_list.append(zhconv.convert(item["item"]["parentName"] + "外观", 'zh-cn')) \
            if item["item"]["parentName"] != "" \
            else temp_list.append(zhconv.convert(item["item"]["parentName"], 'zh-cn'))
        temp_list.append(
            item["item"]["rarenessLevel"]["name"].replace("Superior", "传奇").replace("Enhanced",
                                                                                    "精英").replace(
                "Standard", "特殊"))
        temp_list.append(
            item["item"]["images"]["Png1024xANY"].replace(
                "[BB_PREFIX]", "https://eaassets-a.akamaihd.net/battlelog/battlebinary"
            )
        )
        SE_list.append(temp_list)
    # 保存/获取皮肤图片路径
    i = 0
    while i < len(SE_list):
        SE_list[i][4] = await download_skin(SE_list[i][4])
        i += 1
    # 制作图片,总大小:2351*1322,黑框间隔为8,黑框尺寸220*292，第一张黑框距左边界39，上边界225，武器尺寸为180*45,第一个钱币图片的位置是72*483
    # 交换的背景图
    bg_img = Image.open('app/data/battlefield/pic/bg/SE_bg.png')
    draw = ImageDraw.Draw(bg_img)

    # 字体路径
    font_path = 'app/data/battlefield/font/BFText-Regular-SC-19cf572c.ttf'
    price_font = ImageFont.truetype(font_path, 18)
    seName_font = ImageFont.truetype(font_path, 13)
    seSkinName_font = ImageFont.truetype(font_path, 18)
    # 保存路径
    SavePic = f"app/data/battlefield/exchange/{jh_time}.png"
    x = 59
    y = 340
    for i in range(len(SE_list)):
        while y + 225 < 1322:
            while x + 220 < 2351 and i < len(SE_list):
                if SE_list[i][3] == "特殊":
                    i += 1
                    continue
                # 从上到下分别是武器图片、武器名字、皮肤名字、品质、价格
                # [300, '魯特斯克戰役', 'SMG 08/18', '特殊', 'https://eaassets-a.akamaihd.net/battlelog/battlebinary/gamedata/Tunguska/123/1/U_MAXIMSMG_BATTLEPACKS_FABERGE_T1S3_LARGE-7b01c879.png']
                # 打开交换图像
                SE_png = Image.open(SE_list[i][4]).convert('RGBA')
                # 武器名字
                draw.text((x, y + 52), SE_list[i][2], (169, 169, 169), font=seName_font)
                # 皮肤名字
                draw.text((x, y + 79), SE_list[i][1], (255, 255, 255), font=seSkinName_font)
                # 如果品质为传奇则品质颜色为(255, 132, 0)，精英则为(74, 151, 255)，特殊则为白色
                XD_skin_list = ["菲姆", "菲姆特", "索得格雷",
                                "巴赫馬奇", "菲力克斯穆勒", "狼人", "黑貓",
                                "苟白克", "比利‧米契尔", "在那边", "飞蛾扑火", "佛伦",
                                "默勒谢什蒂", "奥伊图兹", "埃丹", "滨海努瓦耶勒", "唐登空袭",
                                "青春誓言", "德塞夫勒", "克拉奥讷之歌", "芙萝山德斯", "死去的君王",
                                "波佐洛", "奧提加拉山", "奧托‧迪克斯", "保罗‧克利", "阿莫斯‧怀德",
                                "集合点", "法兰兹‧马克", "风暴", "我的机枪", "加利格拉姆", "多贝尔多",
                                "茨纳河", "莫纳斯提尔", "科巴丁", "德•奇里诃", "若宫丸", "波珀灵厄",
                                "K连", "玛德蓉", "巨马", "罗曼诺卡夫", "薩利卡米什", "贝利库尔隧道",
                                "史特拉姆", "阿道戴", "克里夫兰", "家乡套件", "夏日套件", "监禁者",
                                "罗曼诺夫卡", "阿涅森", "波珀灵厄", "威玛猎犬", "齐格飞防线",
                                "华盛顿", "泰罗林猎犬", "怪奇之物", "法兰兹‧马克", "风暴"]
                if SE_list[i][3] == "传奇":
                    if SE_list[i][0] in [270, 300]:
                        draw.text((x, y + 110), f"{SE_list[i][3]}(限定)", (255, 132, 0), font=price_font)
                    elif SE_list[i][1] in XD_skin_list:
                        draw.text((x, y + 110), f"{SE_list[i][3]}(限定)", (255, 132, 0), font=price_font)
                    else:
                        draw.text((x, y + 110), SE_list[i][3], (255, 132, 0), font=price_font)
                    # 打开特效图像
                    tx_png = Image.open('app/data/battlefield/pic/tx/1.png').convert('RGBA')
                elif SE_list[i][1] in XD_skin_list:
                    draw.text((x, y + 110), f"{SE_list[i][3]}(限定)", (255, 132, 0), font=price_font)
                    # 打开特效图像
                    tx_png = Image.open('app/data/battlefield/pic/tx/2.png').convert('RGBA')
                else:
                    draw.text((x, y + 110), SE_list[i][3], (74, 151, 255), font=price_font)
                    # 打开特效图像
                    tx_png = Image.open('app/data/battlefield/pic/tx/2.png').convert('RGBA')
                # 特效图片拉伸
                tx_png = tx_png.resize((100, 153), Image.ANTIALIAS)
                # 特效图片拼接
                bg_img.paste(tx_png, (x + 36, y - 105), tx_png)
                # 武器图片拉伸
                SE_png = SE_png.resize((180, 45), Image.ANTIALIAS)
                # 武器图片拼接
                bg_img.paste(SE_png, (x, y - 45), SE_png)
                # 价格
                draw.text((x + 24, y + 134), str(SE_list[i][0]), (255, 255, 255), font=price_font)
                x += 228
                i += 1
                # bg_img.show()
            y += 298
            x = 59
    bg_img.save(SavePic, 'png', quality=100)
    logger.info("更新交换缓存成功!")
    img_url = await bot.client.create_asset(f'{file_path}')
    await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
    await msg.reply(f"\n更新日期:{file_path[file_path.rfind('/') + 1:].replace('.png', '')}")    
# TODO bf1百科
@bot.command(name='bf1_baike',aliases=['百科','bf1百科'])
async def bf1_baike(msg:Message,item_index:str=None):
    resv_message = msg.content.replace(" ", '').replace("/bf1百科", "").replace("/百科", "").replace("+", "")
    if resv_message == "":
        await msg.reply(
            f"回复 /bf1百科+类型 可查看对应信息\n支持类型:武器、载具、战略、战争、全世界"
            # graia_Image(url=send_temp[1])
        )
        return True
    logger.info(resv_message)
    if resv_message == "武器":
        img_url = await bot.client.create_asset(f'app/data/battlefield/pic/百科/百科武器.jpg')
        await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
        return True
    if resv_message == "载具":
        img_url = await bot.client.create_asset("app/data/battlefield/pic/百科/百科载具.jpg")
        await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
        return True
    if resv_message == "战略":
        img_url = await bot.client.create_asset(path="app/data/battlefield/pic/百科/百科战略.jpg")
        await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
        return True
    if resv_message == "战争":
        img_url = await bot.client.create_asset("app/data/battlefield/pic/百科/百科战争.jpg")
        await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
        return True
    if resv_message == "全世界":
        img_url = await bot.client.create_asset("app/data/battlefield/pic/百科/百科全世界.jpg")
        await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
        return True
    # TODO -bf1百科 序号 ->先读缓存 如果没有就制图
    # 如果序号不对就寄
    # noinspection PyBroadException
    try:
        item_index = int(item_index) - 1
        if item_index > 309 or item_index < 0:
            raise Exception
        await msg.reply(
            f"查询ing"
        )
    except Exception as e:
        logger.error(e)
        await msg.reply(
            f"请检查序号范围:1~310"
        )
        return True
    file_path = f"app/data/battlefield/百科/data.json"
    with open(file_path, 'r', encoding="utf-8") as file1:
        baike_data = json.load(file1)["result"]
    item_list = []
    # i = 1
    for item in baike_data:
        for item2 in item["awards"]:
            item_list.append(item2)
    baike_item = eval(zhconv.convert(str(item_list[item_index]), 'zh-cn'))
    item_path = f"app/data/battlefield/pic/百科/{baike_item['code']}.png"
    if os.path.exists(item_path):
        img_url = await bot.client.create_asset(item_path)
        await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
        return True
    # 底图选择
    if len(baike_item["codexEntry"]["description"]) < 500:
        bg_img_path = f"app/data/battlefield/pic/百科/百科短底.png"
        bg2_img_path = f"app/data/battlefield/pic/百科/百科短.png"
        n_number = 704
    elif 900 > len(baike_item["codexEntry"]["description"]) > 500:
        bg_img_path = f"app/data/battlefield/pic/百科/百科中底.png"
        bg2_img_path = f"app/data/battlefield/pic/百科/百科中.png"
        n_number = 1364
    else:
        bg_img_path = f"app/data/battlefield/pic/百科/百科长底.png"
        bg2_img_path = f"app/data/battlefield/pic/百科/百科长.png"
        n_number = 2002
    bg_img = Image.open(bg_img_path)
    bg2_img = Image.open(bg2_img_path)
    draw = ImageDraw.Draw(bg_img)
    # 百科图片下载
    baike_pic_path = await download_baike(
        baike_item['codexEntry']['images']['Png640xANY'].replace("[BB_PREFIX]",
                                                                 "https://eaassets-a.akamaihd.net/battlelog/battlebinary")
    )
    if baike_pic_path is None:
        await msg.reply(
            f"图片下载失败,请稍后再试!"
        )
        return True
    baike_pic = Image.open(baike_pic_path)
    # 拼接百科图片
    bg_img.paste(baike_pic, (37, 37), baike_pic)
    # 拼接第二层背景图
    bg_img.paste(bg2_img, (0, 0), bg2_img)

    # 颜色
    # 左下角浅灰黄
    # 164，155，108
    # 右边橘色
    # 195，150，60

    # 字体路径
    font_path = 'app/data/battlefield/font/BFText-Regular-SC-19cf572c.ttf'
    # font_path = r'C:\Windows\Fonts\simkai.ttf'
    font1 = ImageFont.truetype(font_path, 30)
    font2 = ImageFont.truetype(font_path, 38)
    font3 = ImageFont.truetype(font_path, 30)
    font4 = ImageFont.truetype(font_path, 20)
    font5 = ImageFont.truetype(font_path, 22)
    # name_font = ImageFont.truetype(font_path, 45)
    # content_font = ImageFont.truetype(font_path, 40)
    # 先制作左下角的文字
    draw.text((60, 810), baike_item['codexEntry']['category'], (164, 155, 108), font=font1)
    draw.text((60, 850), baike_item['name'], (164, 155, 108), font=font2)
    # 右边上面的文字
    draw.text((730, 40), baike_item['codexEntry']['category'], font=font3)
    draw.text((730, 75), baike_item['name'], (255, 255, 255), font=font2)
    draw.text((730, 133), baike_item['criterias'][0]['name'], (195, 150, 60), font=font4)
    new_input = ""
    i = 0
    for letter in baike_item['codexEntry']['description']:
        if letter == "\n":
            new_input += letter
            i = 0
        elif i * 11 % n_number == 0 or (i + 1) * 11 % n_number == 0:
            new_input += '\n'
            i = 0
        i += get_width(ord(letter))
        new_input += letter
    # draw.text((730, 160), re.sub(r"(.{32})", "\\1\n", baike_item['codexEntry']['description']), font=font5)
    # draw.text((730, 160), baike_item['codexEntry']['description'], font=font5)
    draw.text((730, 160), new_input, font=font5)
    bg_img.save(item_path, 'png', quality=100)
    try:
        img_url = await bot.client.create_asset(item_path)
        await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
    except Exception as e:
        logger.error(e)
    return True

             