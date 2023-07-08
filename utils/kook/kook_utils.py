from utils.kook.database import KOOKDB
from functools import wraps
from loguru import logger
from khl import PublicMessage
import datetime
def msg_log():
    def decorator(fn):
        @wraps(fn)
        async def rev_logger(msg: PublicMessage, *args, **kwargs):
            await KOOKDB.add_log(msg.author.id,msg.author.nickname,msg.channel.name,datetime.datetime.now(),msg.guild.master_id,msg.content.strip().replace('\n', '\\n'))
            logger.info(
                f"收到来自 服务器[{msg.guild.master_id}] 频道{msg.channel.name} "
                f"用户{msg.author.nickname}[{msg.author.id}(状态{msg.author.status})] 的消息: " + msg.content.strip().replace(
                    '\n', '\\n')
            )
            return await fn(msg, *args, **kwargs)
        return rev_logger
    return decorator