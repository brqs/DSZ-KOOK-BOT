from modules.self_contained.bf1_info import  bot
from utils.kook.database import KOOKDB
from khl import  Message
from loguru import logger
import datetime
import re
@bot.command(name='log',aliases=['日志', 'l'],prefixes=['-'])
async def kook_log(msg:Message, kook_id: str ,log_num:int=10):
    try:
        uid=int(re.sub(r"\(met\)(\d+)\(met\)", r"\1", kook_id))
        loglist=await KOOKDB.get_log_by_uid(uid)
        if loglist==None:
            return await msg.reply("未查询到使用记录")
        templist = loglist[0:log_num]
        lens=len(loglist)
        output = f"共查询到{lens}条记录，展示前{log_num}条如下：\n"
        logger.info(f"共查询到{lens}条记录，展示前{log_num}条如下：\n")
        for item in templist:
            nickname = item[1]
            channel = item[3]
            timestamp = item[4].strftime("%Y-%m-%d %H:%M")
            message = item[5]
            output += f"{nickname}在{channel}中于{timestamp}使用了：{message}\n"
    except  Exception   as e:
        logger.exception(e)
    return await msg.reply(output)