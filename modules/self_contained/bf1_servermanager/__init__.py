from utils.bf1.default_account import BF1DA
from utils.bf1.database import BF1DB
from utils.bf1.map_team_info import MapData
from modules.self_contained.kook_log import  bot
from khl import  PublicMessage,MessageTypes
from loguru import logger
import asyncio
from utils.bf1.bf_utils import (get_personas_by_name, check_bind, BTR_get_recent_info,
    BTR_get_match_info, BTR_update_data, bfeac_checkBan, bfban_checkBan, gt_checkVban, gt_bf1_stat, record_api
)
from utils.kook.kook_utils import msg_log,permission_required
from typing import Union, List, Tuple, Dict, Any
import time
import datetime
import zhconv
from PIL import Image as PIL_Image
from PIL import ImageFont, ImageDraw, ImageFilter, ImageEnhance
import difflib
import io
import os
import random
import httpx
import json
import aiohttp
import re
from functools import wraps
@bot.command(name="create_group", aliases=["group"],prefixes=["-"])
@msg_log()
@permission_required(10) 
async def bfgroup_create( msg:PublicMessage,group_name: str=None):
    if group_name is None:
        await msg.reply(
            "请输入bf群组名称"
        )
        return False
    else:
        if await BF1DB.create_kook_group_to_bf1_group(group_name):
            await msg.reply(f"已成功群组{group_name}")
        else:
            await msg.reply(f"群组{group_name}已存在，请勿重复创建")
@bot.command(name="add_group_server_info", aliases=["addserver","as"],prefixes=["-"])
@msg_log()
@permission_required(10) 
async def add_bfgroup_server( msg:PublicMessage,group_name: str,server_name: str,server_guid:str):
    if group_name is None or server_name is None or server_guid is None:
        await msg.reply(
            "命令信息不全，请检查"
        )
        return False
    else:
        if await BF1DB.insert_or_update_bfgroup_server(group_name, server_name, server_guid):
            await msg.reply(
            f"群组{group_name}服务器{server_name}添加或修改成功"
            )
        else:
            await msg.reply(
            f"群组{group_name}服务器{server_name}添加或修改失败"
            )
@bot.command(name="remove_group_server_info", aliases=["removeserver","rs"],prefixes=["-"])
@msg_log()
@permission_required(10) 
async def remove_bfgroup_server( msg:PublicMessage,group_name: str,server_name: str):
    if group_name is None or server_name is None :
        await msg.reply(
            "命令信息不全，请检查"
        )
        return False
    else:
        if await BF1DB.remove_bfgroup_server(group_name, server_name):
            await msg.reply(
            f"群组{group_name}服务器{server_name}移除成功"
            )
        else:
            await msg.reply(
            f"群组{group_name}服务器{server_name}移除失败"
            )
@bot.command(name="list_group_server_info", aliases=["f","ls"],prefixes=["-"])
@msg_log()
async def list_bfgroup_server( msg:PublicMessage,group_name: str="ddf"):
    if group_name is None  :
        await msg.reply(
            "命令信息不全，请检查"
        )
        return False
    else:
        try:
            temp=await BF1DB.list_bfgroup_server(group_name)
            if not temp:
                return await msg.reply("该群组不存在")
            gameid_list=[]
            for i in temp:
                gameid_list.append(i[2])
            # 并发查找
            scrape_index_tasks = [asyncio.ensure_future((await BF1DA.get_api_instance()).getServerDetails(gameid)) for gameid in  gameid_list]    
            tasks = asyncio.gather(*scrape_index_tasks)
            try:
                await tasks
                logger.info(f"查询{group_name}服务器ing")
            except:
                await logger.error("服务器无响应")
                return False
            result = [f"所属群组:{group_name}\n" + "=" * 18]
            counter = 1
            servers = 0
            for i in scrape_index_tasks:
                i = i.result()['result']
                if i == "":
                    counter += 1
                else:
                    result.append(f'\n{counter}#:{i["name"][:20]}\n')
                    人数 = f'人数:{i["slots"]["Soldier"]["current"]}/{i["slots"]["Soldier"]["max"]}'
                    result.append(人数)
                    result.append(f"  收藏:{i['serverBookmarkCount']}\n")
                    result.append(f'排队:{i["slots"]["Queue"]["current"]}       观战:{i["slots"]["Spectator"]["current"]}\n')
                    result.append(
                        f'地图:{i["mapModePretty"]}-{i["mapNamePretty"]}\n'.replace("流血", "流\u200b血").replace("战争", "战\u200b争"))
                    result.append(f"=" * 18)
                    counter += 1
                    servers += 1
        except Exception as e:
            logger.exception(e)
        await msg.reply("".join(i for i in result))
#kick ban unban 三件套
@bot.command(name='kick',aliases=['踢','k'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
@permission_required(4) 
async def kick(msg: PublicMessage,server_rank: str, player_name: str, reason: str='kick by dsz ,join kook appeal'):       
# 字数检测
    if len(reason.encode("utf-8"))>30:
        await msg.reply("原因字数过长(汉字10个以内)")
        return False
    # 获取服务器id信息
    server =await BF1DB.get_bfgroup_server_info_by_server_server_name(server_rank)
    if not server_rank :
        return await msg.reply("踢出失败，群组信息有误")
    server_id = server[0][0]
    server_gameid =server[0][1]
    server_guid=server[0][2]
    # 查验玩家存不存在
    try:
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await  msg.reply("查询出错!{player_info}")
    except:
        await msg.reply("网络出错，请稍后再试")
        return False
    if player_info['personas'] == {}:
        await msg.reply("玩家[{player_name}]不存在")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']
    # 调用踢人的接口
    star_time = time.time()
    result = await (await BF1DA.get_api_instance()).kickPlayer(server_gameid,player_pid, reason)
    end_time = time.time()
    logger.info(f"踢人耗时:{end_time - star_time}秒")
    if type(result) == str:
        await msg.reply(f"{result}")
        return False
    elif type(result) == dict:
        await msg.reply(f"踢出成功!原因:{reason}")
        await BF1DB.add_rsp_log(msg.author_id,msg.author.nickname,server_id,server_guid,server_gameid,player_pid,player_name,"kick",msg.content.strip().replace('\n', '\\n'),datetime.datetime.now())
        return True
    else:
        await msg.reply(f"收到指令:/kick {server_rank} {player_name} {reason}\n但执行出错了")
        return False
@bot.command(name='fkick',aliases=['放逐'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
@permission_required(1) 
async def fkick_no_need_rank(msg: PublicMessage, player_name: str, reason: str='kick by dsz ,join kook appeal'):
    # 字数检测
    if 30 < len(reason.encode("utf-8")):
        await msg.reply("原因字数过长(汉字10个以内)")
        return False
    try:
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await  msg.reply("查询出错!{player_info}")
    except:
        await msg.reply("网络出错，请稍后再试")
        return False
    try:
        if player_info['personas'] == {}:
            await msg.reply("玩家[{player_name}]不存在")
            return False
        player_pid = player_info['personas']['persona'][0]['personaId']
        server_info = await (await BF1DA.get_api_instance()).getServersByPersonaIds(player_pid)
        server_info=server_info["result"][f'{player_pid}']
        if server_info is None:
            await msg.reply(f"{server_info},如果该玩家在线,请指定服务器序号")
            return False
        else:
            server_gid = server_info["gameId"]
            server_guid=server_info["guid"]
            server_sid=""
        logger.info(server_gid)
        result =  await (await BF1DA.get_api_instance()).kickPlayer(server_gid,player_pid, reason)
        if type(result) == str:
            await msg.reply(f"{result}")
            return False
        elif type(result) == dict:
            await msg.reply(f"{player_name}不再被需要了，已经被踢出。")
            await BF1DB.add_rsp_log(msg.author_id,msg.author.nickname,server_sid,server_guid,server_gid,player_pid,player_name,"kick",msg.content.strip().replace('\n', '\\n'),datetime.datetime.now())
            return True
        else:
            await msg.reply(f"收到指令但执行出错了")
            return False  
    except Exception as e:
        logger.exception(e)                 
# 不用指定服务器序号
@bot.command(name='kick_no_need_rank',aliases=['踹','nk'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
@permission_required(4) 
async def kick_no_need_rank(msg: PublicMessage, player_name: str, reason: str='kick by dsz ,join kook appeal'):
    # 字数检测
    if 30 < len(reason.encode("utf-8")):
        await msg.reply("原因字数过长(汉字10个以内)")
        return False
    try:
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await  msg.reply("查询出错!{player_info}")
    except:
        await msg.reply("网络出错，请稍后再试")
        return False
    try:
        if player_info['personas'] == {}:
            await msg.reply("玩家[{player_name}]不存在")
            return False
        player_pid = player_info['personas']['persona'][0]['personaId']
        server_info = await (await BF1DA.get_api_instance()).getServersByPersonaIds(player_pid)
        server_info=server_info["result"][f'{player_pid}']
        if server_info is None:
            await msg.reply(f"{server_info},如果该玩家在线,请指定服务器序号")
            return False
        else:
            server_gid = server_info["gameId"]
            server_guid=server_info["guid"]
            server_sid=""
        logger.info(server_gid)
        result =  await (await BF1DA.get_api_instance()).kickPlayer(server_gid,player_pid, reason)
        if type(result) == str:
            await msg.reply(f"{result}")
            return False
        elif type(result) == dict:
            await msg.reply(f"踢出成功!原因:{reason}")
            await BF1DB.add_rsp_log(msg.author_id,msg.author.nickname,server_sid,server_guid,server_gid,player_pid,player_name,"kick",msg.content.strip().replace('\n', '\\n'),datetime.datetime.now())
            return True
        else:
            await msg.reply(f"收到指令:\\nk {player_name}{reason}\n但执行出错了")
            return False  
    except Exception as e:
        logger.exception(e)                 
@bot.command(name='add_ban',aliases=['ban'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
@permission_required(4) 
async def add_ban(msg: PublicMessage,server_rank: str, player_name: str, reason: str='ban by dsz ,join kook appeal'):
    # 字数检测
    if 45 < len(reason.encode("utf-8")):
        await msg.reply("请控制原因在15个汉字以内!")
        return False
    # 获取服务器id信息
    server =await BF1DB.get_bfgroup_server_info_by_server_server_name(server_rank)
    if not server :
        return await msg.reply("操作失败，群组信息有误")
    server_sid = server[0][0]
    server_gid =server[0][1]
    server_guid=server[0][2]
    # 查验玩家存不存在
    try:
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await  msg.reply("查询出错!{player_info}")
    except:
        await msg.reply("网络出错，请稍后再试")
        return False
    if player_info['personas'] == {}:
        await msg.reply("玩家[{player_name}]不存在")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']
    # 调用ban人的接口
    star_time = time.time()
    result = await (await BF1DA.get_api_instance()).addServerBan(player_pid,server_sid)
    end_time = time.time()
    logger.info(f"ban耗时:{end_time - star_time}秒")
    if type(result) == str:
        await msg.reply(f"{result}")
        return False
    elif type(result) == dict:
        await msg.reply(f"封禁成功!原因:{reason}")
        await BF1DB.add_rsp_log(msg.author_id,msg.author.nickname,server_sid,server_guid,server_gid,player_pid,player_name,"ban",msg.content.strip().replace('\n', '\\n'),datetime.datetime.now())    
        return True
    else:
        await msg.reply(
            f"收到指令:\\ban {server_rank} {player_name} {reason}\n但执行出错了")
        return False
# 解封
@bot.command(name='del_ban',aliases=['unban'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
@permission_required(4) 
async def del_ban(msg: PublicMessage,server_rank: str, player_name: str):
    # 获取服务器id信息
    server =await BF1DB.get_bfgroup_server_info_by_server_server_name(server_rank)
    if not server :
        return await msg.reply("操作失败，群组信息有误")
    server_sid = server[0][0]
    server_gid =server[0][1]
    server_guid=server[0][2]
    # 查验玩家存不存在
    try:
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await  msg.reply("查询出错!{player_info}")
    except:
        await msg.reply("网络出错，请稍后再试")
        return False
    if player_info['personas'] == {}:
        await msg.reply("玩家[{player_name}]不存在")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']   
    # 调用unban人的接口
    star_time = time.time()
    result = await (await BF1DA.get_api_instance()).removeServerBan(player_pid,server_sid)
    end_time = time.time()
    logger.info(f"unban耗时:{end_time - star_time}秒")
    if type(result) == str:
        await msg.reply(f"{result}")
        return False
    elif type(result) == dict:
        await msg.reply(f"解封成功!")
        await BF1DB.add_rsp_log(msg.author_id,msg.author.nickname,server_sid,server_guid,server_gid,player_pid,player_name,"unban",msg.content.strip().replace('\n', '\\n'),datetime.datetime.now())    
        return True
    else:
        await msg.reply(
            f"收到指令:\\unban {server_rank} {player_name} \n但执行出错了")
        return False
# banall
@bot.command(name='add_banall',aliases=['banall', 'bana'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
@permission_required(4) 
async def add_banall(msg: PublicMessage,player_name: str, group_name:str="ddf",reason: str="banall by dsz"):
    # TODO 循环 -> task = ban(id) ->并发 -> 循环 result -> 输出
    # 查验玩家存不存在
    try:
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await  msg.reply("查询出错!{player_info}")
        if player_info['personas'] == {}:
            await msg.reply("玩家[{player_name}]不存在")
            return False
    except:
        await msg.reply("网络出错，请稍后再试")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']   
    player_name = player_info['personas']['persona'][0]['displayName']
     # 字数检测
    if 45 < len(reason.encode("utf-8")):
        await msg.reply("请控制原因在15个汉字以内!")
        return False
    #session_dict
    try:
        j=0
        session_dict={}
        temp=await BF1DB.list_bfgroup_server(group_name)
        if not temp:
            return await msg.reply("该群组不存在")
        sid_list=[str(temp[0][1]),str(temp[1][1])]
        for i in sid_list:
            session_dict[j]={"serverid":i}
            j+=1
        scrape_index_tasks = [
            asyncio.ensure_future(
                 (await BF1DA.get_api_instance()).addServerBan( player_pid,session_dict[k]["serverid"])
            )
            for k in range(j)
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
                await BF1DB.add_rsp_log(msg.author_id,msg.author.nickname,f"{sid_list}","","",player_pid,player_name,"ban",msg.content.strip().replace('\n', '\\n'),datetime.datetime.now()) 
            else:
                banall_result.append(f"{i}服:{result}\n")
        try:
            banall_result[-1] = banall_result[-1].replace("\n", "")
        except:
            pass
        banall_result_str = " ".join(n for n in banall_result)
        await msg.reply(banall_result_str)
    except Exception as e:
        logger.exception(e)
@bot.command(name='del_banall',aliases=['unbanall', 'unbana'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
@permission_required(4) 
async def del_banall(msg: PublicMessage,player_name: str, group_name:str="ddf",reason: str="banall by dsz"):
    # TODO 循环 -> task = ban(id) ->并发 -> 循环 result -> 输出
    # 查验玩家存不存在
    try:
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await  msg.reply("查询出错!{player_info}")
        if player_info['personas'] == {}:
            await msg.reply("玩家[{player_name}]不存在")
            return False
    except:
        await msg.reply("网络出错，请稍后再试")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']   
    player_name = player_info['personas']['persona'][0]['displayName']
     # 字数检测
    if 45 < len(reason.encode("utf-8")):
        await msg.reply("请控制原因在15个汉字以内!")
        return False
    #session_dict
    try:
        j=0
        session_dict={}
        temp=await BF1DB.list_bfgroup_server(group_name)
        if not temp:
            return await msg.reply("该群组不存在")
        sid_list=[str(temp[0][1]),str(temp[1][1])]
        for i in sid_list:
            session_dict[j]={"serverid":i}
            j+=1
        scrape_index_tasks = [
            asyncio.ensure_future(
                 (await BF1DA.get_api_instance()).removeServerBan( player_pid,session_dict[k]["serverid"])
            )
            for k in range(j)
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
                    f"{i + 1}服:解除封禁成功!\n"
                )
                await BF1DB.add_rsp_log(msg.author_id,msg.author.nickname,f"{sid_list}","","",player_pid,player_name,"unban",msg.content.strip().replace('\n', '\\n'),datetime.datetime.now()) 
            else:
                unbanall_result.append(f"{i}服:{result}\n")
        try:
            unbanall_result[-1] = unbanall_result[-1].replace("\n", "")
        except:
            pass
        banall_result_str = " ".join(n for n in unbanall_result)
        await msg.reply(banall_result_str)
    except Exception as e:
        logger.exception(e)
@bot.command(name='move_player',aliases=['move', '换边','挪'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
@permission_required(4) 
async def move_player(msg: PublicMessage,server_rank: str, player_name: str, team_index: str):
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
    server =await BF1DB.get_bfgroup_server_info_by_server_server_name(server_rank)
    if not server :
        return await msg.reply("换边失败，群组信息有误")
    server_sid = server[0][0]
    server_gid =server[0][1]
    server_guid=server[0][2]
    # 查验玩家存不存在
    try:
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await  msg.reply("查询出错!{player_info}")
    except:
        await msg.reply("网络出错，请稍后再试")
        return False
    if player_info['personas'] == {}:
        await msg.reply("玩家[{player_name}]不存在")
        return False
    player_pid = player_info['personas']['persona'][0]['personaId']
    # 调用挪人的接口
    try:
        result = await (await BF1DA.get_api_instance()).movePlayer(server_gid, int(player_pid), team_index)
    except:
        await msg.reply(f"网络出错,请稍后再试!")
        return False
    if type(result) == str:
        if "成功" in result:
            await msg.reply(f"更换玩家队伍成功")
            await BF1DB.add_rsp_log(msg.author_id,msg.author.nickname,server_sid,server_guid,server_gid,player_pid,player_name,"move",msg.content.strip().replace('\n', '\\n'),datetime.datetime.now())    
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
@bot.command(name='change_map',aliases=['map', '换图'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
@permission_required(4) 
async def change_map(msg:PublicMessage,server_rank: str, map_index: str):
    # 获取服务器id信息
    server =await BF1DB.get_bfgroup_server_info_by_server_server_name(server_rank)
    if not server :
        return await msg.reply("换图失败，群组信息有误")
    server_sid = server[0][0]
    server_gid =server[0][1]
    server_guid=server[0][2]
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
        result = await (await BF1DA.get_api_instance()).getServerDetails(server_gid)
        if type(result) == str:
            await msg.reply(f"获取图池出错!")
            return False
        i = 0
        result=result['result']
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
            return False
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
    result = await (await BF1DA.get_api_instance()).chooseLevel(server_guid, map_index)
    if type(result) == str:
        await msg.reply(f"{result}")
        return False
    elif type(result) == dict:
        if not map_list:
            await msg.reply(
                f"成功更换服务器{server_rank}地图"
            )
            await BF1DB.add_rsp_log(msg.author_id,msg.author.nickname,server_sid,server_guid,server_gid,"","","map",msg.content.strip().replace('\n', '\\n'),datetime.datetime.now())    
            return True
        else:
            await msg.reply(
                f"成功更换服务器{server_rank}地图为:{map_list[int(map_index)]}".replace('流血', '流\u200b血').replace('\n', '')
            )
            await BF1DB.add_rsp_log(msg.author_id,msg.author.nickname,server_sid,server_guid,server_gid,"","","map",msg.content.strip().replace('\n', '\\n'),datetime.datetime.now())
            return True
    else:
        await msg.reply(f"收到指令:(\map {server_rank}\n但执行出错了")
        return False  
# 图池序号换图
@bot.command(name='change_map_bylist',aliases=['maplist', '图池','ml'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
async def change_map_bylist(msg: PublicMessage,server_rank: str):
    # 获取服务器id信息
    server =await BF1DB.get_bfgroup_server_info_by_server_server_name(server_rank)
    if not server :
        return await msg.reply("查询失败，群组信息有误")
    server_sid = server[0][0]
    server_gid =server[0][1]
    server_guid=server[0][2] 
    # 获取地图池
    result = await (await BF1DA.get_api_instance()).getServerDetails(server_gid)
    if type(result) == str:
        await msg.reply(f"获取图池时网络出错!")
        return False
    map_list = []
    choices = []
    i = 0
    result=result['result']
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
# 查ban列表
@bot.command(name='get_banList',aliases=['banlist', 'bl'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
async def get_banList(msg:PublicMessage,server_rank: str):
    # 获取服务器id信息
    server =await BF1DB.get_bfgroup_server_info_by_server_server_name(server_rank)
    if not server :
        return await msg.reply("查询失败，群组信息有误")
    server_sid = server[0][0]
    server_gid =server[0][1]
    server_guid=server[0][2] 

    # 获取服务器信息-fullInfo
    try:
        server_fullInfo = await (await BF1DA.get_api_instance()).getFullServerDetails(server_gid)
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
@bot.command(name='get_adminList',aliases=['adminlist', 'al'],prefixes=['/','\\','-','、','.','。'])
@msg_log()
async def get_adminList(msg:PublicMessage, server_rank: str):
    # 获取服务器id信息
    server =await BF1DB.get_bfgroup_server_info_by_server_server_name(server_rank)
    if not server :
        return await msg.reply("查询失败，群组信息有误")
    server_sid = server[0][0]
    server_gid =server[0][1]
    server_guid=server[0][2] 
    # 获取服务器信息-fullInfo
    # 获取服务器信息-fullInfo
    try:
        server_fullInfo = await (await BF1DA.get_api_instance()).getFullServerDetails(server_gid)
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
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=header, data=json.dumps(data), timeout=5)
        null=None
        response = eval(response.text)
    except Exception as e:
        logger.error(e)
        return "网络错误"  # 返回空值表示获取玩家列表失败
    if type(server_gameid) != list:
        if str(server_gameid) in response["data"]:
            return response["data"][str(server_gameid)] if response["data"][
                                                               str(server_gameid)] != '' else "服务器信息为空!"
        else:
            return f"获取服务器信息失败:{response}"
    else:
        return response["data"]
@bot.command(name="who_are_playing",aliases=["谁在玩","谁在捞"],prefixes=['/','\\','-','、','.','。'])
@msg_log()
async def who_are_playing(msg:PublicMessage, server_rank: str='ddf1'):
 # 获取服务器id信息
    server =await BF1DB.get_bfgroup_server_info_by_server_server_name(server_rank)
    if not server :
        return await msg.reply("查询失败，群组信息有误")
    server_sid = server[0][0]
    server_gid =server[0][1]
    server_guid=server[0][2] 
# 获取服务器信息-fullInfo
    try:
        server_fullInfo = await (await BF1DA.get_api_instance()).getFullServerDetails(str(server_gid))
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
    # easb接口:
    logger.info(server_gid)
    playerlist_data = await get_playerList_byGameid(server_gid)
    if type(playerlist_data) != dict:
        return await msg.reply(str(playerlist_data))
    playerlist_data["teams"] = {
        0: [item for item in playerlist_data["players"] if item["team"] == 0],
        1: [item for item in playerlist_data["players"] if item["team"] == 1]
    }
    update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(playerlist_data["time"]))
    team1_num = len(playerlist_data["teams"][0])
    team2_num = len(playerlist_data["teams"][1])

    # 用来装服务器玩家
    player_list1 = {}
    player_list2 = {}
    i = 0
    while i < team1_num:
        player_list1[f'[{playerlist_data["teams"][0][i]["rank"]}]{playerlist_data["teams"][0][i]["display_name"]}'] = \
            "%s" % playerlist_data["teams"][0][i]["time"]
        i += 1
    i = 0
    while i < team2_num:
        player_list2[f'[{playerlist_data["teams"][1][i]["rank"]}]{playerlist_data["teams"][1][i]["display_name"]}'] = \
            "%s" % playerlist_data["teams"][1][i]["time"]
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
    group_member_list = await BF1DB.get_group_bindList()
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

    if player_num != 0:
        player_list_filter[-1] = player_list_filter[-1].replace("\n", '')
        await msg.reply(
            f"服内群友数:{player_num}\n" if "捞" not in msg.content else f"服内捞b数:{player_num}\n", player_list_filter,
            f"\n{update_time}"
        )
    else:
        await msg.reply(
            f"服内群友数:0", f"\n{update_time}"
        )
async def download_serverMap_pic(url: str) -> str:
    file_name = './data/battlefield/pic/map/' + url[url.rfind('/') + 1:]
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
    file_path = f"./data/battlefield/游戏模式/data.json"
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
    team_pic_list = os.listdir(f"./data/battlefield/pic/team/")
    for item in team_pic_list:
        if team_name in item:
            return f"./data/battlefield/pic/team/{item}"


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
@bot.command(name="pl",aliases=["pl","玩家列表"],prefixes=['/','\\','-','、','.','。'])
@msg_log()
async def get_server_playerList_pic(msg:PublicMessage, server_rank: str="ddf1"):
    # 获取服务器id信息
    server =await BF1DB.get_bfgroup_server_info_by_server_server_name(server_rank)
    if not server :
        return await msg.reply("查询失败，群组信息有误")
    server_sid = server[0][0]
    server_gid =server[0][1]
    server_guid=server[0][2] 
    await msg.reply(
        f"查询ing"

    )
    try:
        time_start = time.time()
        try:
            server_info = await (await BF1DA.get_api_instance()).getFullServerDetails(server_gid)
            if server_info == '':
                raise Exception
        except:
            logger.error("服务器无响应")
            return False
        admin_pid_list = [str(item['personaId']) for item in server_info['result']["rspInfo"]["adminList"]]
        admin_counter = 0
        admin_color = (0, 255, 127)
        vip_pid_list = [str(item['personaId']) for item in server_info['result']["rspInfo"]["vipList"]]
        vip_counter = 0
        vip_color = (255, 99, 71)
        bind_pid_list = await BF1DB.get_group_bindList()
        bind_color = (179, 244, 255)
        bind_counter = 0
        max_level_counter = 0

        server_info = await (await BF1DA.get_api_instance()).getFullServerDetails(server_gid)
        if not server_info:
            return await msg.reply("获取服务器信息失败~")
        server_info =server_info['result']
        playerlist_data = await get_playerList_byGameid(server_gid)
        if type(playerlist_data) != dict:
            return await msg.reply("服务器为空")
        playerlist_data["teams"] = {
            0: [item for item in playerlist_data["players"] if item["team"] == 0],
            1: [item for item in playerlist_data["players"] if item["team"] == 1]
        }
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(playerlist_data["time"]))

        # 获取玩家生涯战绩
        # 队伍1
        scrape_index_tasks_t1 = [asyncio.ensure_future((await BF1DA.get_api_instance()).detailedStatsByPersonaId(player_item['pid'])) for
                                player_item in playerlist_data["teams"][0]]
        tasks = asyncio.gather(*scrape_index_tasks_t1)
        try:
            await tasks
        except:
            pass

        # 队伍2
        scrape_index_tasks_t2 = [asyncio.ensure_future((await BF1DA.get_api_instance()).detailedStatsByPersonaId(player_item['pid'])) for
                                player_item in playerlist_data["teams"][1]]
        tasks = asyncio.gather(*scrape_index_tasks_t2)
        try:
            await tasks
        except:
            pass

        # 服务器名
        server_name = server_info["serverInfo"]["name"]
        # MP_xxx
        server_mapName = server_info["serverInfo"]["mapName"]

        team1_name = MapData.MapTeamDict[server_info["serverInfo"]["mapName"]]["Team1"]
        team1_pic = get_team_pic(team1_name)
        team1_pic = PIL_Image.open(team1_pic).convert('RGBA')
        team1_pic = team1_pic.resize((40, 40), PIL_Image.ANTIALIAS)
        team2_name = MapData.MapTeamDict[server_info["serverInfo"]["mapName"]]["Team2"]
        team2_pic = get_team_pic(team2_name)
        team2_pic = PIL_Image.open(team2_pic).convert('RGBA')
        team2_pic = team2_pic.resize((40, 40), PIL_Image.ANTIALIAS)

        # 地图路径
        server_map_pic = await get_server_map_pic(server_mapName)
        # 地图作为画布底图并且高斯模糊化
        if server_map_pic is None:
            logger.warning(f"获取地图{server_mapName}图片出错")
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
        Ping1 = PIL_Image.open(f"./data/battlefield/pic/ping/4.png").convert('RGBA')
        Ping1 = Ping1.resize((int(Ping1.size[0] * 0.04), int(Ping1.size[1] * 0.04)), PIL_Image.ANTIALIAS)
        Ping2 = PIL_Image.open(f"./data/battlefield/pic/ping/3.png").convert('RGBA')
        Ping2 = Ping2.resize((int(Ping2.size[0] * 0.04), int(Ping2.size[1] * 0.04)), PIL_Image.ANTIALIAS)
        Ping3 = PIL_Image.open(f"./data/battlefield/pic/ping/2.png").convert('RGBA')
        Ping3 = Ping3.resize((int(Ping3.size[0] * 0.04), int(Ping3.size[1] * 0.04)), PIL_Image.ANTIALIAS)
        Ping4 = PIL_Image.open(f"./data/battlefield/pic/ping/1.png").convert('RGBA')
        Ping4 = Ping4.resize((int(Ping4.size[0] * 0.04), int(Ping4.size[1] * 0.04)), PIL_Image.ANTIALIAS)
        Ping5 = PIL_Image.open(f"./data/battlefield/pic/ping/0.png").convert('RGBA')
        Ping5 = Ping5.resize((int(Ping5.size[0] * 0.04), int(Ping5.size[1] * 0.04)), PIL_Image.ANTIALIAS)

        draw = ImageDraw.Draw(IMG)
        # 字体路径
        font_path = './data/battlefield/font/BFText-Regular-SC-19cf572c.ttf'
        title_font = ImageFont.truetype(font_path, 40)
        team_font = ImageFont.truetype(font_path, 25)
        title_font_small = ImageFont.truetype(font_path, 22)
        player_font = ImageFont.truetype(font_path, 20)
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
        for i, player_item in enumerate(playerlist_data["teams"][0]):
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
            if str(player_item["display_name"]).upper() in bind_pid_list:
                color_temp = bind_color
                bind_counter += 1
            if str(player_item["pid"]) in vip_pid_list:
                color_temp = vip_color
                vip_counter += 1
            if str(player_item["pid"]) in admin_pid_list:
                color_temp = admin_color
                admin_counter += 1
            # if player_item["platoon"] != "":
            #     draw.text((195, 155 + i * 23), f"[{player_item['platoon']}]{player_item['name']}", fill=color_temp,
            #               font=player_font)
            # else:
            draw.text((195, 155 + i * 23), player_item["display_name"], fill=color_temp, font=player_font)

            # 延迟 靠右显示
            ping_pic = Ping5
            if player_item['ping'] <= 50:
                ping_pic = Ping1
            elif 50 < player_item['ping'] <= 100:
                ping_pic = Ping2
            elif 100 < player_item['ping'] <= 150:
                ping_pic = Ping3
            elif 150 < player_item['ping']:
                ping_pic = Ping4
            IMG.paste(ping_pic, (880, 158 + i * 23), ping_pic)
            draw.text((930, 155 + i * 23), f"{player_item['ping']}", anchor="ra", fill='white', font=player_font)

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
        for i, player_item in enumerate(playerlist_data["teams"][1]):
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
            if str(player_item["display_name"]).upper() in bind_pid_list:
                color_temp = bind_color
                bind_counter += 1
            if str(player_item["pid"]) in vip_pid_list:
                color_temp = vip_color
                vip_counter += 1
            if str(player_item["pid"]) in admin_pid_list:
                color_temp = admin_color
                admin_counter += 1
            # if player_item["platoon"] != "":
            #     draw.text((1055, 155 + i * 23), f"[{player_item['platoon']}]{player_item['name']}", fill=color_temp,
            #               font=player_font)
            # else:
            draw.text((1055, 155 + i * 23), player_item["display_name"], fill=color_temp, font=player_font)
            # 延迟 靠右显示
            ping_pic = Ping5
            if player_item['ping'] <= 50:
                ping_pic = Ping1
            elif 50 < player_item['ping'] <= 100:
                ping_pic = Ping2
            elif 100 < player_item['ping'] <= 150:
                ping_pic = Ping3
            elif 150 < player_item['ping']:
                ping_pic = Ping4
            IMG.paste(ping_pic, (1740, 158 + i * 23), ping_pic)
            draw.text((1790, 155 + i * 23), f"{player_item['ping']}", anchor="ra", fill='white', font=player_font)
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

        i_temp = len(playerlist_data['teams'][0]) if len(playerlist_data['teams'][0]) >= len(
            playerlist_data['teams'][1]) else len(playerlist_data['teams'][1])
        avg_color = (250, 183, 39)
        avg_1_1 = 0
        avg_1_2 = 0
        avg_1_3 = 0
        avg_1_4 = 0
        avg_1_5 = 0
        if len(playerlist_data['teams'][0]) != 0:
            avg_1_1 = int(RANK_counter1 / len(playerlist_data['teams'][0]))
            avg_1_2 = KD_counter1 / len(playerlist_data['teams'][0])
            avg_1_3 = KPM_counter1 / len(playerlist_data['teams'][0])
            avg_1_4 = TIME_counter1 / len(playerlist_data['teams'][0])
            avg_1_5 = int(WIN_counter1 / len(playerlist_data['teams'][0]))
        avg_2_1 = 0
        avg_2_2 = 0
        avg_2_3 = 0
        avg_2_4 = 0
        avg_2_5 = 0
        if len(playerlist_data['teams'][1]) != 0:
            avg_2_1 = int(RANK_counter2 / len(playerlist_data['teams'][1]))
            avg_2_2 = KD_counter2 / len(playerlist_data['teams'][1])
            avg_2_3 = KPM_counter2 / len(playerlist_data['teams'][1])
            avg_2_4 = TIME_counter2 / len(playerlist_data['teams'][1])
            avg_2_5 = int(WIN_counter2 / len(playerlist_data['teams'][1]))

        if leve_position_1:
            rank_font_temp = ImageFont.truetype(font_path, 15)
            ascent, descent = rank_font_temp.getsize(f"{int(RANK_counter1 / len(playerlist_data['teams'][0]))}")
            leve_position_1 = 168 - ascent / 2, 156 + i_temp * 23
            draw.text((115, 156 + i_temp * 23), f"平均:",
                    fill="white",
                    font=player_font)
            if RANK_counter1 != 0:
                draw.text(leve_position_1, f"{int(RANK_counter1 / len(playerlist_data['teams'][0]))}",
                        fill=avg_color if avg_1_1 > avg_2_1 else "white",
                        font=player_font)
            if WIN_counter1 != 0:
                draw.text((565, 156 + i_temp * 23), f"{int(WIN_counter1 / len(playerlist_data['teams'][0]))}%",
                        anchor="ra",
                        fill=avg_color if avg_1_5 > avg_2_5 else "white",
                        font=player_font)
            if KD_counter1 != 0:
                draw.text((645, 156 + i_temp * 23),
                        "{:.2f}".format(KD_counter1 / len(playerlist_data['teams'][0])),
                        anchor="ra",
                        fill=avg_color if avg_1_2 > avg_2_2 else "white",
                        font=player_font)
            if KPM_counter1 != 0:
                draw.text((740, 156 + i_temp * 23),
                        "{:.2f}".format(KPM_counter1 / len(playerlist_data['teams'][0])),
                        anchor="ra",
                        fill=avg_color if avg_1_3 > avg_2_3 else "white",
                        font=player_font)
            if TIME_counter1 != 0:
                draw.text((850, 156 + i_temp * 23),
                        "{:.1f}".format(TIME_counter1 / len(playerlist_data['teams'][0])),
                        anchor="ra",
                        fill=avg_color if avg_1_4 > avg_2_4 else "white",
                        font=player_font)

        if leve_position_2:
            rank_font_temp = ImageFont.truetype(font_path, 15)
            ascent, descent = rank_font_temp.getsize(f"{int(RANK_counter1 / len(playerlist_data['teams'][1]))}")
            leve_position_2 = 1028 - ascent / 2, 156 + i_temp * 23
            draw.text((975, 156 + i_temp * 23), f"平均:",
                    fill="white",
                    font=player_font)
            if RANK_counter2 != 0:
                draw.text(leve_position_2, f"{int(RANK_counter2 / len(playerlist_data['teams'][1]))}",
                        fill=avg_color if avg_1_1 < avg_2_1 else "white",
                        font=player_font)
            if WIN_counter2 != 0:
                draw.text((1425, 156 + i_temp * 23), f"{int(WIN_counter2 / len(playerlist_data['teams'][1]))}%",
                        anchor="ra",
                        fill=avg_color if avg_1_5 < avg_2_5 else "white",
                        font=player_font)
            if KD_counter2 != 0:
                draw.text((1505, 156 + i_temp * 23),
                        "{:.2f}".format(KD_counter2 / len(playerlist_data['teams'][1])),
                        anchor="ra",
                        fill=avg_color if avg_1_2 < avg_2_2 else "white",
                        font=player_font)
            if KPM_counter2 != 0:
                draw.text((1600, 156 + i_temp * 23),
                        "{:.2f}".format(KPM_counter2 / len(playerlist_data['teams'][1])),
                        anchor="ra",
                        fill=avg_color if avg_1_3 < avg_2_3 else "white",
                        font=player_font)
            if TIME_counter2 != 0:
                draw.text((1710, 156 + i_temp * 23),
                        "{:.1f}".format(TIME_counter2 / len(playerlist_data['teams'][1])),
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

@bot.command(name="bf1log",aliases=["bf1log","blog"],prefixes=['/','\\','-','、','.','。'])
@permission_required(1) 
async def bf1log(msg:PublicMessage,player_name:str):
    bf1_log=await BF1DB.get_bf1log_by_player_name(player_name)
    if bf1_log is None:
        await msg.reply("不存在该玩家被操作的记录")
    else:
        output="="*18+"\n"
        for i in bf1_log:
            output+=f'{player_name}于{i[3]}被{i[0]}{i[1]}具体记录为{i[4]}\n'
        output+="="*18
        await msg.reply(output)
  
@bot.command(name="add_group_admin",aliases=["agd","ad"],prefixes=['/','\\','-','、','.','。'])
@permission_required(8) 
async def add_group_admin(msg:PublicMessage,group_name:str,kook:str):
    try:   
        uid=int(re.sub(r"\(met\)(\d+)\(met\)", r"\1", kook))
        user=await bot.client.fetch_user(uid)
        nick=user.nickname
        await BF1DB.insert_or_update_bfgroup_server_admin(group_name,uid,nick,4)
        await msg.reply("添加管理员成功")
    except Exception as e:
        logger.exception(e)
  
@bot.command(name="add_group_owner",aliases=["ago","ao"],prefixes=['/','\\','-','、','.','。'])
@permission_required(16) 
async def add_group_owner(msg:PublicMessage,group_name:str,kook:str):
    try:   
        uid=int(re.sub(r"\(met\)(\d+)\(met\)", r"\1", kook))
        user=await bot.client.fetch_user(uid)
        nick=user.nickname
        await BF1DB.insert_or_update_bfgroup_server_admin(group_name,uid,nick,8)
        await msg.reply("添加所有者成功")
    except Exception as e:
        logger.exception(e)
 
@bot.command(name="del_group_admin",aliases=["dga","da"],prefixes=['/','\\','-','、','.','。'])
@permission_required(8)  
async def del_group_admin(msg:PublicMessage,group_name:str,kook:str):
    try:   
        uid=int(re.sub(r"\(met\)(\d+)\(met\)", r"\1", kook))
        user=await bot.client.fetch_user(uid)
        nick=user.nickname
        await BF1DB.delete_bfgroup_server_admin(group_name,uid,nick,4)
        await msg.reply("移除管理员成功")
    except Exception as e:
        logger.exception(e)
       
@bot.command(name="del_group_owner",aliases=["dgo","do"],prefixes=['/','\\','-','、','.','。'])
@permission_required(8) 
async def del_group_owner(msg:PublicMessage,group_name:str,kook:str):
    try:   
        uid=int(re.sub(r"\(met\)(\d+)\(met\)", r"\1", kook))
        user=await bot.client.fetch_user(uid)
        nick=user.nickname
        await BF1DB.delete_bfgroup_server_admin(group_name,uid,nick,8)
        await msg.reply("移除所有者成功")
    except Exception as e:
        logger.exception(e)

@bot.command(name="list_group_admin",aliases=["lga","la"],prefixes=['/','\\','-','、','.','。'])
@permission_required(1)
async def list_group_admin(msg:PublicMessage,group_name:str):
    try:   
        admin_list=await BF1DB.list_bfgroup_server_admin(group_name)
        if admin_list is None:
            await msg.reply("该群组不存在")
        logger.info(admin_list)
        output=f"{group_name}共有{len(admin_list)}位管理，列出如下\n"
        output+="="*16+"\n"
        for i in admin_list:
            output +=f"{i[0]}{'(所有者)'if i[1]==8 else ''}\n"
        output+="="*16
        await msg.reply(output)
    except Exception as e:
        logger.exception(e)
