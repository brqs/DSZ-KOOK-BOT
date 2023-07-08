from utils.bf1.data_handle import WeaponData, VehicleData, ServerData
from utils.bf1.default_account import BF1DA
from utils.bf1.draw import PlayerStatPic, PlayerVehiclePic, PlayerWeaponPic, Exchange
from utils.bf1.gateway_api import api_instance
from utils.bf1.map_team_info import MapData
from utils.bf1.database import BF1DB
from utils.bf1.bf_utils import (get_personas_by_name, check_bind, BTR_get_recent_info,
    BTR_get_match_info, BTR_update_data, bfeac_checkBan, bfban_checkBan, gt_checkVban, gt_bf1_stat, record_api
)
from utils.kook.kook_utils import msg_log
from core.bot import bot
from khl import Bot, Message,MessageTypes
from loguru import logger
import asyncio
import io
import zhconv
import re
import time
from typing import List, Tuple
import datetime
import math
from pathlib import Path
from rapidfuzz import fuzz
import json
from PIL import Image as PIL_Image
@bot.command(name='Bind',aliases=['bind', '绑定'],prefixes=['-'])
@msg_log()
async def Bind(msg:Message, player_name: str):
    if player_name is None:
        await msg.reply("你不告诉我游戏名字绑啥呢\n示例:/绑定 <你的游戏名字>" )
        return False
    player_name = player_name.replace("+", "").replace(" ", "").replace("<", "").replace(">", "")
    player_info = await get_personas_by_name(player_name)
    if isinstance(player_info, str):
        return await  msg.reply("查询出错!{player_info}")
    if not player_info:
        return await msg.reply(f"玩家 {player_name} 不存在")
    pid = player_info["personas"]["persona"][0]["personaId"]
    uid = player_info["personas"]["persona"][0]["pidId"]
    display_name = player_info["personas"]["persona"][0]["displayName"]
    # name = player_info["personas"]["persona"][0]["name"]
    # dateCreated = player_info["personas"]["persona"][0]["dateCreated"]
    # lastAuthenticated = player_info["personas"]["persona"][0]["lastAuthenticated"]
    # 进行比对，如果大写后的玩家名不一致，返回错误
    if player_name.upper() != display_name.upper():
        return await msg.reply(f"玩家 {player_name} 不存在")
    # 查询绑定信息，如果有旧id就获取旧id
    old_display_name = None
    old_pid = None
    old_uid = None
    if bind_info := await check_bind(msg.author_id):
        if isinstance(bind_info, str):
            return await msg.reply(f"查询出错!{bind_info}")
        old_display_name = bind_info.get("displayName")
        old_pid = bind_info.get("pid")
        old_uid = bind_info.get("uid")
    # 写入玩家绑定信息
    try:
        await BF1DB.bind_player_kook(msg.author_id, pid)
        if old_display_name and (old_pid != pid):
            result = f"绑定ID变更!\ndisplayName: {old_display_name}\n -> {display_name}\npid: {old_pid}\n -> {pid}\nuid: {old_uid}\n -> {uid}"
        else:
            result = f"绑定成功!你的信息如下:\ndisplayName: {display_name}\npid: {pid}\nuid: {uid}"
        return await msg.reply(result)
    except Exception as e:
        logger.error(e)
        return await msg.reply("绑定失败!")
@bot.command(name='info',aliases=['信息'],prefixes=['-'])
@msg_log()
async def info(msg:Message, player_name: str=None):
    # 如果没有参数，查询绑定信息
    if  player_name==None :
        if not (bind_info := await check_bind(msg.author_id)):
            return await msg.reply("你还没有绑定!请使用'-绑定 玩家名'进行绑定!")
        if isinstance(bind_info, str):
            return await msg.reply(f"查询出错!{bind_info}")
        display_name = bind_info.get("displayName")
        pid = bind_info.get("pid")
        uid = bind_info.get("uid")
        return await msg.reply(
                f"你的信息如下:\n"+
                f"玩家名: {display_name}\n"+
                f"pid: {pid}\n"+
                f"uid: {uid}"
            )
    else:
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await msg.reply(f"查询出错!{player_info}")
        if not player_info:
            return await msg.reply(f"玩家 {player_name} 不存在")
        pid = player_info["personas"]["persona"][0]["personaId"]
        uid = player_info["personas"]["persona"][0]["pidId"]
        display_name = player_info["personas"]["persona"][0]["displayName"]
        # name = player_info["personas"]["persona"][0]["name"]
        # dateCreated = player_info["personas"]["persona"][0]["dateCreated"]
        # lastAuthenticated = player_info["personas"]["persona"][0]["lastAuthenticated"]
        return await msg.reply(
                f"玩家名: {display_name}\n"+
                f"pid: {pid}\n"+
                f"uid: {uid}\n"
            )
@bot.command(name='stat',aliases=['生涯','生涯'],prefixes=['-'])
@msg_log()
async def player_stat_pic(msg: Message,player_name: str=None):
    # 如果没有参数，查询绑定信息,获取display_name
    if player_name!=None:
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await msg.reply(f"查询出错!{player_info}")
        if not player_info:
            return await msg.reply(f"玩家 {player_name} 不存在")
        player_pid = player_info["personas"]["persona"][0]["personaId"]
        display_name = player_info["personas"]["persona"][0]["displayName"]
    elif bind_info := await check_bind(msg.author_id):
        if isinstance(bind_info, str):
            return await msg.reply(f"查询出错!{bind_info}")
        display_name = bind_info.get("displayName")
        player_pid = bind_info.get("pid")
    else:
        return await msg.reply("你还没有绑定!请使用'-绑定 玩家名'进行绑定!")
    await msg.reply("查询ing")

    # 并发获取生涯、武器、载具信息
    tasks = [
        (await BF1DA.get_api_instance()).detailedStatsByPersonaId(player_pid),
        (await BF1DA.get_api_instance()).getWeaponsByPersonaId(player_pid),
        (await BF1DA.get_api_instance()).getVehiclesByPersonaId(player_pid),
        bfeac_checkBan(display_name)
    ]
    tasks = await asyncio.gather(*tasks)

    # 检查返回结果
    player_stat, player_weapon, player_vehicle, eac_info = tasks[0], tasks[1], tasks[2], tasks[3]
    if isinstance(player_stat, str):
        logger.error(player_stat)
        return await msg.reply(f"查询出错!{player_stat}")
    else:
        player_stat: dict
        player_stat["result"]["displayName"] = display_name
    if isinstance(player_weapon, str):
        logger.error(player_weapon)
        return await msg.reply(f"查询出错!{player_weapon}")
    else:
        player_weapon: list = WeaponData(player_weapon).filter()
    if isinstance(player_vehicle, str):
        logger.error(player_vehicle)
        return await msg.reply(f"查询出错!{player_vehicle}")
    else:
        player_vehicle: list = VehicleData(player_vehicle).filter()

    # 生成图片
    player_stat_img = await PlayerStatPic(player_stat, player_weapon, player_vehicle).draw()
    if player_stat_img:
        img = player_stat_img #pil合成的对象
        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        imgByte = io.BytesIO(imgByteArr.getvalue())
        img_url = await bot.client.create_asset(imgByte)
        await msg.reply(img_url,type=MessageTypes.IMG)
        
    # 发送文字
    # 包含等级、游玩时长、击杀、死亡、KD、胜局、败局、胜率、KPM、SPM、步战击杀、载具击杀、技巧值、最远爆头距离
    # 协助击杀、最高连杀、复活数、治疗数、修理数、狗牌数
    player_info = player_stat["result"]
    rank = player_info.get('basicStats').get('rank')
    # 转换成xx小时xx分钟
    time_seconds = player_info.get('basicStats').get('timePlayed')
    time_played = f"{time_seconds // 3600}小时{time_seconds % 3600 // 60}分钟"
    kills = player_info.get('basicStats').get('kills')
    deaths = player_info.get('basicStats').get('deaths')
    kd = round(kills / deaths, 2) if deaths else kills
    wins = player_info.get('basicStats').get('wins')
    losses = player_info.get('basicStats').get('losses')
    # 百分制
    win_rate = round(wins / (wins + losses) * 100, 2) if wins + losses else 100
    kpm = player_info.get('basicStats').get('kpm')
    spm = player_info.get('basicStats').get('spm')
    vehicle_kill = sum(item["killsAs"] for item in player_info["vehicleStats"])
    vehicle_kill = int(vehicle_kill)
    infantry_kill = int(player_info['basicStats']['kills'] - vehicle_kill)
    skill = player_info.get('basicStats').get('skill')
    longest_headshot = player_info.get('longestHeadShot')
    killAssists = int(player_info.get('killAssists'))
    highestKillStreak = int(player_info.get('highestKillStreak'))
    revives = int(player_info.get('revives'))
    heals = int(player_info.get('heals'))
    repairs = int(player_info.get('repairs'))
    dogtagsTaken = int(player_info.get('dogtagsTaken'))
    eac_info = (
        f'{eac_info.get("stat")}\n案件地址:{eac_info.get("url")}\n'
        if eac_info.get("stat")
        else "未查询到EAC信息\n"
    )
    result = [
        f"玩家:{display_name}\n"
        f"等级:{rank or 0}\n"
        f"游玩时长:{time_played}\n"
        f"击杀:{kills}  死亡:{deaths}  KD:{kd}\n"
        f"胜局:{wins}  败局:{losses}  胜率:{win_rate}%\n"
        f"KPM:{kpm}  SPM:{spm}\n"
        f"步战击杀:{infantry_kill}  载具击杀:{vehicle_kill}\n"
        f"技巧值:{skill}\n"
        f"最远爆头距离:{longest_headshot}米\n"
        f"协助击杀:{killAssists}  最高连杀:{highestKillStreak}\n"
        f"复活数:{revives}   治疗数:{heals}\n"
        f"修理数:{repairs}   狗牌数:{dogtagsTaken}\n"
        f"EAC状态:{eac_info}" + "=" * 18
    ]
    weapon = player_weapon[0]
    name = zhconv.convert(weapon.get('name'), 'zh-hans')
    kills = int(weapon["stats"]["values"]["kills"])
    seconds = weapon["stats"]["values"]["seconds"]
    kpm = "{:.2f}".format(kills / seconds * 60) if seconds != 0 else kills
    acc = (
        round(
            weapon["stats"]["values"]["hits"]
            / weapon["stats"]["values"]["shots"]
            * 100,
            2,
        )
        if weapon["stats"]["values"]["shots"] != 0
        else 0
    )
    hs = round(weapon["stats"]["values"]["headshots"] / weapon["stats"]["values"]["kills"] * 100, 2) \
        if weapon["stats"]["values"]["kills"] != 0 else 0
    eff = round(weapon["stats"]["values"]["hits"] / weapon["stats"]["values"]["kills"], 2) \
        if weapon["stats"]["values"]["kills"] != 0 else 0
    time_played = "{:.1f}H".format(seconds / 3600)
    result.append(
        f"最佳武器:{name}\n"
        f"击杀: {kills}\tKPM: {kpm}\n"
        f"命中率: {acc}%\t爆头率: {hs}%\n"
        f"效率: {eff}\t时长: {time_played}\n"
        + "=" * 18
    )

    vehicle = player_vehicle[0]
    name = zhconv.convert(vehicle["name"], 'zh-cn')
    kills = vehicle["stats"]["values"]["kills"]
    seconds = vehicle["stats"]["values"]["seconds"]
    kpm = "{:.2f}".format(kills / seconds * 60) if seconds != 0 else kills
    destroyed = vehicle["stats"]["values"]["destroyed"]
    time_played = "{:.1f}H".format(vehicle["stats"]["values"]["seconds"] / 3600)
    result.append(
        f"最佳载具:{name}\n"
        f"击杀:{kills}\tKPM:{kpm}\n"
        f"摧毁:{destroyed}\t时长:{time_played}\n"
        + "=" * 18
    )
    result = "\n".join(result)
    return await msg.reply(result)
def has_chinese(string):
    """
    判断字符串是否含有中文字符
    """
    pattern = re.compile(r'[\u4e00-\u9fa5]')
    match = pattern.search(string)
    return match is not None
@bot.command(name='weapon',aliases=['weapon', "武器", "weapon", "wp", "精英兵", "机枪", "轻机枪", "步枪", "狙击枪", "装备", "配备",
                "半自动步枪", "半自动", "手榴弹", "手雷", "投掷物", "霰弹枪", "散弹枪", "驾驶员", "坦克驾驶员",
                "冲锋枪", "佩枪", "手枪", "近战", "突击兵", "土鸡兵", "土鸡", "突击",
                "侦察兵", "侦察", "斟茶兵", "斟茶", "医疗兵", "医疗", "支援兵", "支援"],prefixes=['-'])
@msg_log()
async def weapon(msg:Message,player_name: str=None,weapon_name:str=None,row:str="4",col:str="1",sort_type:str=""):
    # 如果没有参数，查询绑定信息,获取display_name
    weapon_type=msg.content.split()[0][1:]
    if player_name!=None :
        if has_chinese(player_name):
            bind_info = await check_bind(msg.author_id)
            if isinstance(bind_info, str):
                return await msg.reply(f"查询出错!{bind_info}")
            display_name = bind_info.get("displayName")
            player_pid = bind_info.get("pid")
            weapon_name=player_name
        else:
            player_info = await get_personas_by_name(player_name)
            if isinstance(player_info, str):
                return await msg.reply(f"查询出错!{player_info}")
            if not player_info:
                return await msg.reply(f"玩家 {player_name} 不存在")
            player_pid = player_info["personas"]["persona"][0]["personaId"]
            display_name = player_info["personas"]["persona"][0]["displayName"]
    elif bind_info := await check_bind(msg.author_id):
        if isinstance(bind_info, str):
            return await msg.reply(f"查询出错!{bind_info}")
        display_name = bind_info.get("displayName")
        player_pid = bind_info.get("pid")
    else:
        return await msg.reply("你还没有绑定!请使用'-绑定 玩家名'进行绑定!")
    await msg.reply("查询ing")

    # 获取武器信息
    player_weapon = await (await BF1DA.get_api_instance()).getWeaponsByPersonaId(player_pid)
    if isinstance(player_weapon, str):
        logger.error(player_weapon)
        return await msg.reply(f"查询出错!{player_weapon}")
    else:
        if  weapon_name==None:
            player_weapon: list = WeaponData(player_weapon).filter(
                rule=weapon_type if weapon_type else "",
                sort_type=sort_type if sort_type else "",
            )
        else:
            player_weapon: list = WeaponData(player_weapon).search_weapon(
                weapon_name,
                sort_type=sort_type if sort_type else "",
            )
            if not player_weapon:
                return await msg.reply(f"没有找到武器[{weapon_name}]哦~")

    # 生成图片
    player_weapon_img = (
        await PlayerWeaponPic(weapon_data=player_weapon).draw_search(
            display_name, row, col
        )
        if weapon_name
        else await PlayerWeaponPic(weapon_data=player_weapon).draw(
            display_name, row, col
        )
    )
    if player_weapon_img:
        img = player_weapon_img #pil合成的对象
        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        imgByte = io.BytesIO(imgByteArr.getvalue())
        img_url = await bot.client.create_asset(imgByte)
        return await msg.reply(img_url,type=MessageTypes.IMG)
    # 发送文字数据
    result = [f"玩家: {display_name}\n" + "=" * 18]
    for weapon in player_weapon:
        if not weapon.get("stats").get('values'):
            continue
        name = zhconv.convert(weapon.get('name'), 'zh-hans')
        kills = int(weapon["stats"]["values"]["kills"])
        seconds = weapon["stats"]["values"]["seconds"]
        kpm = "{:.2f}".format(kills / seconds * 60) if seconds != 0 else kills
        acc = (
            round(
                weapon["stats"]["values"]["hits"]
                / weapon["stats"]["values"]["shots"]
                * 100,
                2,
            )
            if weapon["stats"]["values"]["shots"] != 0
            else 0
        )
        hs = round(weapon["stats"]["values"]["headshots"] / weapon["stats"]["values"]["kills"] * 100, 2) \
            if weapon["stats"]["values"]["kills"] != 0 else 0
        eff = round(weapon["stats"]["values"]["hits"] / weapon["stats"]["values"]["kills"], 2) \
            if weapon["stats"]["values"]["kills"] != 0 else 0
        time_played = "{:.1f}H".format(seconds / 3600)
        result.append(
            f"{name}\n"
            f"击杀: {kills}\tKPM: {kpm}\n"
            f"命中率: {acc}%\t爆头率: {hs}%\n"
            f"效率: {eff}\t时长: {time_played}\n"
            + "=" * 18
        )
    result = result[:5]
    result = "\n".join(result)
    return await msg.reply(result)
@bot.command(name='vehicle',aliases=["载具", "vehicle", "vc", "坦克", "地面", "飞机", "飞船", "飞艇", "空中", "海上", "定点", "巨兽", "机械巨兽"],prefixes=['-'])
@msg_log()
async def vehicle(msg:Message,player_name: str=None,vehicle_name:str=None,row:str="4",col:str="1",sort_type:str=""):
    vehicle_type=msg.content.split()[0][1:]
    # 如果没有参数，查询绑定信息,获取display_name
    if player_name!=None:
        if has_chinese(player_name):
            bind_info = await check_bind(msg.author_id)
            if isinstance(bind_info, str):
                return await msg.reply(f"查询出错!{bind_info}")
            display_name = bind_info.get("displayName")
            player_pid = bind_info.get("pid")
            vehicle_name=player_name
        else:
            player_info = await get_personas_by_name(player_name)
            if isinstance(player_info, str):
                return await msg.reply(f"查询出错!{player_info}")
            if not player_info:
                return await msg.reply(f"玩家 {player_name} 不存在")
            player_pid = player_info["personas"]["persona"][0]["personaId"]
            display_name = player_info["personas"]["persona"][0]["displayName"]
    elif bind_info := await check_bind(msg.author_id):
        if isinstance(bind_info, str):
            return await msg.reply(f"查询出错!{bind_info}")
        display_name = bind_info.get("displayName")
        player_pid = bind_info.get("pid")
    else:
        return await msg.reply("你还没有绑定!请使用'-绑定 玩家名'进行绑定!")
    await msg.reply("查询ing")

    # 获取载具信息
    player_vehicle = await (await BF1DA.get_api_instance()).getVehiclesByPersonaId(player_pid)
    if isinstance(player_vehicle, str):
        logger.error(player_vehicle)
        return await msg.reply(f"查询出错!{player_vehicle}")
    else:
        if not vehicle_name:
            player_vehicle: list = VehicleData(player_vehicle).filter(
                rule=vehicle_type if vehicle_type else "",
                sort_type=sort_type if sort_type else "",
            )
        else:
            player_vehicle: list = VehicleData(player_vehicle).search_vehicle(
                target_vehicle_name=vehicle_name,
                sort_type=sort_type if sort_type else "",
            )
            if not player_vehicle:
                return await msg.reply(f"没有找到载具[{vehicle_name}]哦~")

    # 生成图片
    player_vehicle_img = (
        await PlayerVehiclePic(vehicle_data=player_vehicle).draw_search(
            display_name, row, col
        )
        if vehicle_name
        else await PlayerVehiclePic(vehicle_data=player_vehicle).draw(
            display_name, row, col
        )
    )
    if player_vehicle_img:
        img = player_vehicle_img #pil合成的对象
        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        imgByte = io.BytesIO(imgByteArr.getvalue())
        img_url = await bot.client.create_asset(imgByte)
        return await msg.reply(img_url,type=MessageTypes.IMG)
    # 发送文字数据
    result = [f"玩家: {display_name}\n" + "=" * 18]
    for vehicle in player_vehicle:
        name = zhconv.convert(vehicle["name"], 'zh-cn')
        kills = int(vehicle["stats"]["values"]["kills"])
        seconds = vehicle["stats"]["values"]["seconds"]
        kpm = "{:.2f}".format(kills / seconds * 60) if seconds != 0 else kills
        destroyed = int(vehicle["stats"]["values"]["destroyed"])
        time_played = "{:.1f}H".format(vehicle["stats"]["values"]["seconds"] / 3600)
        result.append(
            f"{name}\n"
            f"击杀:{kills}\tKPM:{kpm}\n"
            f"摧毁:{destroyed}\t时长:{time_played}\n"
            + "=" * 18
        )
    result = result[:5]
    result = "\n".join(result)
    return await msg.reply(
            result
        )
@bot.command(name='recent',aliases=['最近战绩'],prefixes=['-'])
@msg_log()
async def player_recent_info(
        msg: Message,
        player_name: str
):
    # 如果没有参数，查询绑定信息,获取display_name
    if player_name:
        player_name = player_name
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await msg.reply(f"查询出错!{player_info}")
        if not player_info:
            return await msg.reply(f"玩家 {player_name} 不存在")
        # player_pid = player_info["personas"]["persona"][0]["personaId"]
        display_name = player_info["personas"]["persona"][0]["displayName"]
    elif bind_info := await check_bind(msg.author_id):
        if isinstance(bind_info, str):
            return await msg.reply(f"查询出错!{bind_info}")
        display_name = bind_info.get("displayName")
        # player_pid = bind_info.get("pid")
    else:
        return await msg.reply("你还没有绑定!请使用'-绑定 玩家名'进行绑定!")
    await msg.reply("查询ing")

    # 从BTR获取数据
    try:
        player_recent = await BTR_get_recent_info(display_name)
        if not player_recent:
            return await msg.reply("没有查询到最近记录哦~")
        result = [f"玩家: {display_name}\n" + "=" * 15]
        result.extend(
            f"{item['time']}\n"
            f"得分: {item['score']}\nSPM: {item['spm']}\n"
            f"KD: {item['kd']}  KPM: {item['kpm']}\n"
            f"游玩时长: {item['time_play']}\n局数: {item['win_rate']}\n" + "=" * 15
            for item in player_recent[:3]
        )
        return await msg.reply("\n".join(result))
    except Exception as e:
        logger.error(e)
        return await msg.reply("查询出错!")


# 对局数据
@bot.command(name='match',aliases=['对局','最近'],prefixes=['-'])
@msg_log()
async def player_match_info(
        msg: Message,
        player_name: str=None
):
    # 如果没有参数，查询绑定信息,获取display_name
    if player_name:
        player_name = player_name
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await msg.reply(f"查询出错!{player_info}")
        if not player_info:
            return await msg.reply(f"玩家 {player_name} 不存在")
        # player_pid = player_info["personas"]["persona"][0]["personaId"]
        display_name = player_info["personas"]["persona"][0]["displayName"]
    elif bind_info := await check_bind(msg.author_id):
        if isinstance(bind_info, str):
            return await msg.reply(f"查询出错!{bind_info}")
        display_name = bind_info.get("displayName")
        # player_pid = bind_info.get("pid")
    else:
        return await msg.reply("你还没有绑定!请使用'-绑定 玩家名'进行绑定!")
    await msg.reply("查询ing")

    # 从BTR获取数据
    try:
        await BTR_update_data(display_name)
        player_match = await BTR_get_match_info(display_name)
        if not player_match:
            return await msg.reply("没有查询到对局记录哦~")
        result = [f"玩家: {display_name}\n" + "=" * 15]
        # 处理数据
        for item in player_match:
            players = item.get("players")
            for player in players:
                if player.get("player_name").upper() == display_name.upper():
                    game_info = item.get("game_info")
                    # 如果得为0则跳过
                    if player["score"] == 0:
                        continue
                    map_name = game_info['map_name']
                    player["team_name"] = f"Team{player['team_name']}" if player["team_name"] else "No Team"
                    team_name = next(
                        (
                            MapData.MapTeamDict.get(key).get(
                                player["team_name"], "No Team"
                            )
                            for key in MapData.MapTeamDict
                            if MapData.MapTeamDict.get(key).get("Chinese") == map_name
                        ),
                        "No Team",
                    )
                    team_win = "🏆" if player['team_win'] else "🏳"
                    result.append(
                        f"服务器: {game_info['server_name'][:20]}\n"
                        f"时间: {game_info['game_time'].strftime('%Y年%m月%d日 %H:%M')}\n"
                        f"地图: {game_info['map_name']}-{game_info['mode_name']}\n"
                        f"队伍: {team_name}  {team_win}\n"
                        f"击杀: {player['kills']}\t死亡: {player['deaths']}\n"
                        f"KD: {player['kd']}\tKPM: {player['kpm']}\n"
                        f"得分: {player['score']}\tSPM: {player['spm']}\n"
                        f"命中率: {player['accuracy']}\t爆头: {player['headshots']}\n"
                        f"游玩时长: {player['time_played']}\n"
                        + "=" * 15
                    )
        result = result[:4]
        result = "\n".join(result)
        await msg.reply(result)
    except Exception as e:
        logger.error(e)
        return await msg.reply("查询出错!")





# 搜服务器
@bot.command(name='search_server',aliases=['搜服务器','ss'],prefixes=['-'])
@msg_log()
async def search_server(
        msg: Message,
        server_name: str
):
    server_name = server_name
    # 调用接口获取数据
    filter_dict = {"name": server_name}
    server_info = await (await BF1DA.get_api_instance()).searchServers(server_name, filter_dict=filter_dict)
    if isinstance(server_info, str):
        return await msg.reply(f"查询出错!{server_info}")
    else:
        server_info = server_info["result"]

    if not (server_list := ServerData(server_info).sort()):
        return await msg.reply("没有搜索到服务器哦~")
    result = []
    # 只显示前10个
    if len(server_list) > 10:
        result.append(f"搜索到{len(server_list)}个服务器,显示前10个\n" + "=" * 20)
        server_list = server_list[:10]
    else:
        result.append(f"搜索到{len(server_list)}个服务器\n" + "=" * 20)
    result.extend(
        f"{server.get('name')[:25]}\n"
        f"人数: {server.get('SoldierCurrent')}/{server.get('SoldierMax')}"
        f"[{server.get('QueueCurrent')}]({server.get('SpectatorCurrent')})\n"
        f"地图: {server.get('map_name')}-{server.get('mode_name')}\n"
        f"GameId: {server.get('game_id')}\n" + "=" * 20
        for server in server_list
    )
    result = "\n".join(result)
    return await msg.reply(result)


# 详细服务器
@bot.command(name='detailed_server',aliases=['详细服务器','ds'],prefixes=['-'])
@msg_log()
async def detailed_server(
        msg: Message,
        game_id: str
):
    game_id = game_id
    if not game_id.isdigit():
        return await msg.reply("GameId必须为数字!")

    # 调用接口获取数据
    server_info = await (await BF1DA.get_api_instance()).getFullServerDetails(game_id)
    if isinstance(server_info, str):
        return await msg.reply(f"查询出错!{server_info}")
    else:
        server_info = server_info["result"]

    # 处理数据
    # 第一部分为serverInfo,其下:包含服务器名、简介、人数、地图、模式、gameId、guid、收藏数serverBookmarkCount
    # 第二部分为rspInfo,其下包含owner（名字和pid）、serverId、createdDate、expirationDate、updatedDate
    # 第三部分为platoonInfo，其下包含战队名、tag、人数、description
    result = []
    Info = server_info["serverInfo"]
    result.append(
        f"服务器: {Info.get('name')}\n"
        f"人数: {Info.get('slots').get('Soldier').get('current')}/{Info.get('slots').get('Soldier').get('max')}"
        f"[{Info.get('slots').get('Queue').get('current')}]({Info.get('slots').get('Spectator').get('current')})\n"
        f"地图: {Info.get('mapNamePretty')}-{Info.get('mapModePretty')}\n"
        f"简介: {Info.get('description')}\n"
        f"GameId: {Info.get('gameId')}\n"
        f"Guid: {Info.get('guid')}\n"
        + "=" * 20
    )
    if rspInfo := server_info.get("rspInfo"):
        result.append(
            f"ServerId:{rspInfo.get('server').get('serverId')}\n"
            f"创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(rspInfo['server']['createdDate']) / 1000))}\n"
            f"到期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(rspInfo['server']['expirationDate']) / 1000))}\n"
            f"更新时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(rspInfo['server']['updatedDate']) / 1000))}\n"
            f"服务器拥有者: {rspInfo.get('owner').get('name')}\n"
            f"Pid: {rspInfo.get('owner').get('pid')}\n"
            + "=" * 20
        )
    if platoonInfo := server_info.get("platoonInfo"):
        result.append(
            f"战队: [{platoonInfo.get('tag')}]{platoonInfo.get('name')}\n"
            f"人数: {platoonInfo.get('soldierCount')}\n"
            f"简介: {platoonInfo.get('description')}\n"
            + "=" * 20
        )
    result = "\n".join(result)
    return await msg.reply(result)


# 定时服务器详细信息收集，每20分钟执行一次
@bot.task.add_interval(minutes=20)
async def server_info_collect():
    time_start = time.time()
    #   搜索获取私服game_id
    tasks = []
    filter_dict = {
        "name": "",  # 服务器名
        "serverType": {  # 服务器类型
            "OFFICIAL": "off",  # 官服
            "RANKED": "on",  # 私服
            "UNRANKED": "on",  # 私服(不计战绩)
            "PRIVATE": "on"  # 密码服
        }
    }
    game_id_list = []
    for _ in range(50):
        tasks.append((await BF1DA.get_api_instance()).searchServers("", filter_dict=filter_dict))
    logger.debug("开始更新私服数据")
    results = await asyncio.gather(*tasks)
    for result in results:
        if isinstance(result, str):
            continue
        result: list = result["result"]
        server_list = ServerData(result).sort()
        for server in server_list:
            if server["game_id"] not in game_id_list:
                game_id_list.append(server["game_id"])
    logger.success(f"共获取{len(game_id_list)}个私服")

    #   获取详细信息
    #   每250个私服分为一组获取详细信息
    tasks = []
    results = []
    for game_id in game_id_list:
        tasks.append((await BF1DA.get_api_instance()).getFullServerDetails(game_id))
        if len(tasks) == 250:
            logger.debug(f"开始获取私服详细信息，共{len(tasks)}个")
            temp = await asyncio.gather(*tasks)
            results.extend(temp)
            tasks = []
    if tasks:
        logger.debug(f"开始获取私服详细信息，共{len(tasks)}个")
        temp = await asyncio.gather(*tasks)
        results.extend(temp)

    results = [result for result in results if not isinstance(result, str)]
    logger.success(f"共获取{len(results)}个私服详细信息")

    #   整理数据
    serverId_list = []
    server_info_list: List[Tuple[str, str, str, int, datetime, datetime, datetime]] = []
    vip_dict = {}
    ban_dict = {}
    admin_dict = {}
    owner_dict = {}
    for result in results:
        server = result["result"]
        rspInfo = server.get("rspInfo", {})
        Info = server["serverInfo"]
        if not rspInfo:
            continue
        server_name = Info["name"]
        server_server_id = rspInfo.get("server", {}).get("serverId")
        server_guid = Info["guid"]
        server_game_id = Info["gameId"]
        serverBookmarkCount = Info["serverBookmarkCount"]
        playerCurrent = Info["slots"]["Soldier"]["current"]
        playerMax = Info["slots"]["Soldier"]["max"]
        playerQueue = Info["slots"]["Queue"]["current"]
        playerSpectator = Info["slots"]["Spectator"]["current"]

        #   将其转换为datetime
        createdDate = rspInfo.get("server", {}).get("createdDate")
        createdDate = datetime.datetime.fromtimestamp(int(createdDate) / 1000)
        expirationDate = rspInfo.get("server", {}).get("expirationDate")
        expirationDate = datetime.datetime.fromtimestamp(int(expirationDate) / 1000)
        updatedDate = rspInfo.get("server", {}).get("updatedDate")
        updatedDate = datetime.datetime.fromtimestamp(int(updatedDate) / 1000)
        server_info_list.append(
            (
                server_name, server_server_id,
                server_guid, server_game_id, serverBookmarkCount,
                createdDate, expirationDate, updatedDate,
                playerCurrent, playerMax, playerQueue, playerSpectator
            )
        )
        serverId_list.append(server_server_id)
        vip_dict[server_server_id] = rspInfo.get("vipList", [])
        ban_dict[server_server_id] = rspInfo.get("bannedList", [])
        admin_dict[server_server_id] = rspInfo.get("adminList", [])
        if owner := rspInfo.get("owner"):
            owner_dict[server_server_id] = [owner]

    #   保存数据
    start_time = time.time()
    await BF1DB.update_serverInfoList(server_info_list)
    logger.debug(f"更新服务器信息完成，耗时{round(time.time() - start_time, 2)}秒")
    start_time = time.time()
    await BF1DB.update_serverVipList(vip_dict)
    logger.debug(f"更新服务器VIP完成，耗时{round(time.time() - start_time, 2)}秒")
    start_time = time.time()
    await BF1DB.update_serverBanList(ban_dict)
    logger.debug(f"更新服务器封禁完成，耗时{round(time.time() - start_time, 2)}秒")
    await BF1DB.update_serverAdminList(admin_dict)
    start_time = time.time()
    logger.debug(f"更新服务器管理员完成，耗时{round(time.time() - start_time, 2)}秒")
    await BF1DB.update_serverOwnerList(owner_dict)
    logger.debug(f"更新服务器所有者完成，耗时{round(time.time() - start_time, 2)}秒")
    logger.success(f"共更新{len(serverId_list)}个私服详细信息，耗时{round(time.time() - time_start, 2)}秒")


# 天眼查
@bot.command(name='tyc',aliases=['天眼查'],prefixes=['-'])
@msg_log()
async def tyc(msg: Message,player_name: str=None):
    # 如果没有参数，查询绑定信息,获取display_name
    if  player_name==None:
        if bind_info := await check_bind(msg.author_id):
            if isinstance(bind_info, str):
                return await msg.reply(f"查询出错!{bind_info}")
            display_name = bind_info.get("displayName")
            player_pid = bind_info.get("pid")
        else:
            return await msg.reply(f"你还没有绑定!请使用'-绑定 玩家名'进行绑定!")
    else:
        player_name = player_name
        player_info = await get_personas_by_name(player_name)
        if isinstance(player_info, str):
            return await msg.reply(f"查询出错!{player_info}")
        if not player_info:
            return await msg.reply(f"玩家 {player_name} 不存在")
        player_pid = player_info["personas"]["persona"][0]["personaId"]
        display_name = player_info["personas"]["persona"][0]["displayName"]

    await msg.reply(f"查询ing")

    send = [f'玩家名:{display_name}\n玩家Pid:{player_pid}\n' + "=" * 20 + '\n']
    # 查询最近游玩、vip/admin/owner/ban数、bfban信息、bfeac信息、正在游玩
    tasks = [
        (await BF1DA.get_api_instance()).mostRecentServers(player_pid),
        bfeac_checkBan(display_name),
        bfban_checkBan(player_pid),
        gt_checkVban(player_pid),
        record_api(player_pid),
        (await BF1DA.get_api_instance()).getServersByPersonaIds(player_pid),
    ]
    tasks = await asyncio.gather(*tasks)
    # 最近游玩
    recent_play_data = tasks[0]
    if not isinstance(recent_play_data, str):
        recent_play_data: dict = recent_play_data
        send.append("最近游玩:\n")
        for data in recent_play_data["result"][:3]:
            send.append(f'{data["name"][:25]}\n')
        send.append("=" * 20 + '\n')
    vip_count = await BF1DB.get_playerVip(player_pid)
    admin_count = await BF1DB.get_playerAdmin(player_pid)
    owner_count = await BF1DB.get_playerOwner(player_pid)
    ban_count = await BF1DB.get_playerBan(player_pid)
    vban_count = tasks[3]
    send.append(
        f"VIP数:{vip_count}\t"
        f"管理数:{admin_count}\n"
        f"BAN数:{ban_count}\t"
        f"服主数:{owner_count}\n"
        f"VBAN数:{vban_count}\n"
        + "=" * 20 + '\n'
    )
    # bfban信息
    bfban_data = tasks[2]
    if bfban_data.get("stat"):
        send.append("BFBAN信息:\n")
        send.append(f'状态:{bfban_data["status"]}\n' + f"案件地址:{bfban_data['url']}\n" if bfban_data.get("url") else "")
        send.append("=" * 20 + '\n')
    # bfeac信息
    bfeac_data = tasks[1]
    if bfeac_data.get("stat"):
        send.append("BFEAC信息:\n")
        send.append(
            f'状态:{bfeac_data["stat"]}\n'
            f'案件地址:{bfeac_data["url"]}\n'
        )
        send.append("=" * 20 + '\n')
    # 小助手标记信息
    record_data = tasks[4]
    try:
        browse = record_data["data"]["browse"]
        hacker = record_data["data"]["hacker"]
        doubt = record_data["data"]["doubt"]
        send.append("战绩软件查询结果:\n")
        send.append(f"浏览量:{browse} ")
        send.append(f"外挂标记:{hacker} ")
        send.append(f"怀疑标记:{doubt}\n")
        send.append("=" * 20 + '\n')
    except:
        pass
    # 正在游玩
    playing_data = tasks[5]
    if not isinstance(playing_data, str):
        playing_data: dict = playing_data["result"]
        send.append("正在游玩:\n")
        if not playing_data[f"{player_pid}"]:
            send.append("玩家未在线/未进入服务器游玩\n")
        else:
            send.append(playing_data[f"{player_pid}"]['name'] + '\n')
        send.append("=" * 20 + '\n')
    # 去掉最后一个换行
    if send[-1] == '\n':
        send = send[:-1]
    return await msg.reply(f"{''.join(send)}")


# 查询排名信息
@bot.command(name='BF1Rank',aliases=['bf1rank'],prefixes=['-'])
@msg_log()
async def BF1Rank(msg: Message,rank_type: str,  name: str=None,page: str=1):
    await msg.reply(f"查询ing")
    if name==None:
        if rank_type in ["收藏", "bookmark"]:
            bookmark_list = await BF1DB.get_server_bookmark()
            if not bookmark_list:
                return await msg.reply(f"没有在数据库中找到服务器收藏信息!")
            # 将得到的数据15个一页分组，如果page超出范围则返回错误,否则返回对应页的数据
            if page > math.ceil(len(bookmark_list) / 15):
                return await msg.reply(f"超出范围!({page}/{math.ceil(len(bookmark_list) / 15)})")
            send = [
                f"服务器收藏排名(page:{page}/{math.ceil(len(bookmark_list) / 15)})",
            ]
            for data in bookmark_list[(page - 1) * 15:page * 15]:
                # 获取服务器排名,组合为: index. serverName[:20] bookmark
                index = bookmark_list.index(data) + 1
                send.append(f"{index}.{data['serverName'][:20]} {data['bookmark']}")
            send = "\n".join(send)
            return await msg.reply(f"{send}")
        elif rank_type in ["vip"]:
            vip_list = await BF1DB.get_allServerPlayerVipList()
            if not vip_list:
                return await msg.reply(f"没有在数据库中找到服务器VIP信息!")
            # 将得到的数据15个一页分组，如果page超出范围则返回错误,否则返回对应页的数据
            # data = [
            #     {
            #         "pid": 123,
            #         "displayName": "xxx",
            #         "server_list": []
            #     }
            # ]
            if page > math.ceil(len(vip_list) / 15):
                return await msg.reply(f"超出范围!({page}/{math.ceil(len(vip_list) / 15)})")
            send = [
                f"服务器VIP排名(page:{page}/{math.ceil(len(vip_list) / 15)})",
            ]
            for data in vip_list[(page - 1) * 15:page * 15]:
                # 获取服务器排名,组合为: index. serverName[:20] bookmark
                index = vip_list.index(data) + 1
                send.append(f"{index}.{data['displayName'][:20]} {len(data['server_list'])}")
            send = "\n".join(send)
            return await msg.reply(f"{send}")
        elif rank_type in ["ban", "封禁"]:
            ban_list = await BF1DB.get_allServerPlayerBanList()
            if not ban_list:
                return await msg.reply(f"没有在数据库中找到服务器封禁信息!")
            # 将得到的数据15个一页分组，如果page超出范围则返回错误,否则返回对应页的数据
            if page > math.ceil(len(ban_list) / 15):
                return await msg.reply(f"超出范围!({page}/{math.ceil(len(ban_list) / 15)})")
            send = [f"服务器封禁排名(page:{page}/{math.ceil(len(ban_list) / 15)})"]
            for data in ban_list[(page - 1) * 15:page * 15]:
                # 获取服务器排名,组合为: index. serverName[:20] bookmark
                index = ban_list.index(data) + 1
                send.append(f"{index}.{data['displayName'][:20]} {len(data['server_list'])}")
            send = "\n".join(send)
            return await msg.reply(f"{send}")
        elif rank_type in ["admin", "管理"]:
            admin_list = await BF1DB.get_allServerPlayerAdminList()
            if not admin_list:
                return await msg.reply(f"没有在数据库中找到服务器管理信息!")
            # 将得到的数据15个一页分组，如果page超出范围则返回错误,否则返回对应页的数据
            if page > math.ceil(len(admin_list) / 15):
                return await msg.reply(f"超出范围!({page}/{math.ceil(len(admin_list) / 15)})")
            send = [
                f"服务器管理排名(page:{page}/{math.ceil(len(admin_list) / 15)})",
            ]
            for data in admin_list[(page - 1) * 15:page * 15]:
                # 获取服务器排名,组合为: index. serverName[:20] bookmark
                index = admin_list.index(data) + 1
                send.append(f"{index}.{data['displayName'][:20]} {len(data['server_list'])}")
            send = "\n".join(send)
            return await msg.reply(f"{send}")
        elif rank_type in ["owner", "服主"]:
            owner_list = await BF1DB.get_allServerPlayerOwnerList()
            if not owner_list:
                return await msg.reply(f"没有在数据库中找到服务器服主信息!")
            # 将得到的数据15个一页分组，如果page超出范围则返回错误,否则返回对应页的数据
            if page > math.ceil(len(owner_list) / 15):
                return await msg.reply(f"超出范围!({page}/{math.ceil(len(owner_list) / 15)})")
            send = [
                f"服务器服主排名(page:{page}/{math.ceil(len(owner_list) / 15)})",
            ]
            for data in owner_list[(page - 1) * 15:page * 15]:
                # 获取服务器排名,组合为: index. serverName[:20] bookmark
                index = owner_list.index(data) + 1
                send.append(f"{index}.{data['displayName'][:20]} {len(data['server_list'])}")
            send = "\n".join(send)
            return await msg.reply(f"{send}")
    else:
        # 查询服务器/玩家对应分类的排名
        if rank_type in ["收藏", "bookmark"]:
            bookmark_list = await BF1DB.get_server_bookmark()
            if not bookmark_list:
                return await msg.reply(f"没有在数据库中找到服务器收藏信息!")
            result = []
            for item in bookmark_list:
                if (fuzz.ratio(name.upper(), item['serverName'].upper()) > 80) or \
                        name.upper() in item['serverName'].upper() or \
                        item['serverName'].upper() in name.upper():
                    result.append(item)
            if not result:
                return await msg.reply(f"没有在数据库中找到该服务器的收藏信息!")
            send = [f"搜索到{len(result)}个结果:" if len(result) <= 15 else f"搜索到超过15个结果,只显示前15个结果!"]
            result = result[:15]
            for data in result:
                # 获取服务器排名,组合为: index. serverName[:20] bookmark
                index = bookmark_list.index(data) + 1
                send.append(f"{index}.{data['serverName'][:20]} {data['bookmark']}")
            send = "\n".join(send)
            return await msg.reply(f"{send}")
        elif rank_type in ["vip"]:
            vip_list = await BF1DB.get_allServerPlayerVipList()
            if not vip_list:
                return await msg.reply(f"没有在数据库中找到服务器VIP信息!")
            display_name = [item['displayName'].upper() for item in vip_list]
            if name.upper() not in display_name:
                return await msg.reply(f"没有在数据库中找到该玩家的VIP信息!")
            index = display_name.index(name.upper()) + 1
            return await msg.reply(f"{name}的VIP排名为{index}")
        elif rank_type in ["ban", "封禁"]:
            ban_list = await BF1DB.get_allServerPlayerBanList()
            if not ban_list:
                return await msg.reply(f"没有在数据库中找到服务器封禁信息!")
            display_name = [item['displayName'].upper() for item in ban_list]
            if name.upper() not in display_name:
                return await msg.reply(f"没有在数据库中找到该玩家的封禁信息!")
            index = display_name.index(name.upper()) + 1
            return await msg.reply(f"{name}的封禁排名为{index}")
        elif rank_type in ["admin", "管理"]:
            admin_list = await BF1DB.get_allServerPlayerAdminList()
            if not admin_list:
                return await msg.reply(f"没有在数据库中找到服务器管理信息!")
            display_name = [item['displayName'].upper() for item in admin_list]
            if name.upper() not in display_name:
                return await msg.reply(f"没有在数据库中找到该玩家的管理信息!")
            index = display_name.index(name.upper()) + 1
            return await msg.reply(f"{name}的管理排名为{index}")
        elif rank_type in ["owner", "服主"]:
            owner_list = await BF1DB.get_allServerPlayerOwnerList()
            if not owner_list:
                return await msg.reply(f"没有在数据库中找到服务器服主信息!")
            display_name = [item['displayName'].upper() for item in owner_list]
            if name.upper() not in display_name:
                return await msg.reply(f"没有在数据库中找到该玩家的服主信息!")
            index = display_name.index(name.upper()) + 1
            return await msg.reply(f"{name}的服主排名为{index}")
# 战地一私服情况
@bot.command(name='bf1_server_info_check',aliases=['bf1'],prefixes=['-'])
@msg_log()
async def bf1_server_info_check(msg:Message):
    result = await gt_bf1_stat()
    if not isinstance(result, str):
        return await msg.reply(f"查询出错!{result}")
    return await msg.reply(f"{result}")
#交换
@bot.command(name='get_exchange',aliases=['交换'],prefixes=['-'])
@msg_log()
async def get_exchange(msg:Message, search_time: str=None):
    # 交换缓存图片的路径
    file_path = Path("./data/battlefield/exchange/")
    # 获取今天的日期
    file_date = datetime.datetime.now()
    date_now = file_date
    # 1.如果文件夹为空,则获取gw api的数据制图
    # 2.如果不为空,直接发送最新的缓存图片
    # 3.发送完毕后从gw api获取数据,如果和缓存的json文件内容一样,则不做任何操作,否则重新制图并保存为今天日期的文件
    if not file_path.exists():
        file_path.mkdir(parents=True)
    if file_path.exists() and len(list(file_path.iterdir())) == 0:
        # 获取gw api的数据
        result = await (await BF1DA.get_api_instance()).getOffers()
        if not isinstance(result, dict):
            return await msg.reply(f"查询出错!{result}")
        # 将数据写入json文件
        with open(file_path / f"{date_now.year}年{date_now.month}月{date_now.day}日.json", 'w',
                  encoding="utf-8") as file1:
            json.dump(result, file1, ensure_ascii=False, indent=4)
        # 将数据制图
        img = await Exchange(result).draw()
        img = PIL_Image(img)
        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        imgByte = io.BytesIO(imgByteArr.getvalue())
        img_url = await bot.client.create_asset(imgByte)
        await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
        return await msg.reply(
                f"更新时间:{date_now.year}年{date_now.month}月{date_now.day}日"
            )
    # 发送缓存里最新的图片
    for day in range(int(len(list(file_path.iterdir()))) + 1):
        file_date = date_now - datetime.timedelta(days=day)
        pic_file_name = f"{file_date.year}年{file_date.month}月{file_date.day}日.png"
        if (file_path / pic_file_name).exists():
            img = Path(f"./data/battlefield/exchange/{pic_file_name}").read_bytes()
            await msg.ctx.channel.send(img_url,type=MessageTypes.IMG)
            await msg.reply(
                f"更新时间:{date_now.year}年{date_now.month}月{date_now.day}日"
            )
            break
    # 获取gw api的数据,更新缓存
    result = await (await BF1DA.get_api_instance()).getOffers()
    if isinstance(result, str):
        return logger.error(f"查询交换出错!{result}")
    # 如果result和之前最新的json文件内容一样,则return
    if (file_path / f"{file_date.year}年{file_date.month}月{file_date.day}日.json").exists():
        with open(file_path / f"{file_date.year}年{file_date.month}月{file_date.day}日.json",
                  'r', encoding="utf-8") as file1:
            data = json.load(file1)
            if data.get("result") == result.get("result"):
                return logger.info("交换未更新~")
            else:
                logger.debug("正在更新交换~")
                # 将数据写入json文件
                with open(file_path / f"{date_now.year}年{date_now.month}月{date_now.day}日.json",
                          'w', encoding="utf-8") as file2:
                    json.dump(result, file2, ensure_ascii=False, indent=4)
                # 将数据制图
                _ = await Exchange(result).draw()
                return logger.success("成功更新交换缓存~")
    else:
        return logger.error(f"未找到交换数据文件{file_date.year}年{file_date.month}月{file_date.day}日.json")
    
# 战役
@bot.command(name='get_CampaignOperations',aliases=['战役'],prefixes=['-'])
@msg_log()
async def get_CampaignOperations(msg:Message):
    data = await (await BF1DA.get_api_instance()).getPlayerCampaignStatus()
    if not isinstance(data, dict):
        return await msg.reply(f"查询出错!{data}")
    if not data.get("result"):
        return await msg.reply(
            f"当前无进行战役信息!"
        )
    return_list = []
    from time import strftime, gmtime
    return_list.append(zhconv.convert(f"战役名称:{data['result']['name']}\n", "zh-cn"))
    return_list.append(zhconv.convert(f'战役描述:{data["result"]["shortDesc"]}\n', "zh-cn"))
    return_list.append('战役地点:')
    place_list = []
    for key in data["result"]:
        if key.startswith("op") and data["result"].get(key):
            place_list.append(zhconv.convert(f'{data["result"][key]["name"]} ', "zh-cn"))
    place_list = ','.join(place_list)
    return_list.append(place_list)
    return_list.append(strftime("\n剩余时间:%d天%H小时%M分", gmtime(data["result"]["minutesRemaining"] * 60)))
    return await msg.reply(
        "".join(n for n in return_list)
    )
