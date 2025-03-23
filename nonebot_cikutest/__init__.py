from .ciku import *
from nonebot import on_message

Group_Message = on_message()

@Group_Message.handle()
async def _(event: GroupMessageEvent):
    msg = event.get_message().extract_plain_text()
    res = await check_input(msg, event)
    if res != None:
        await Group_Message.send(Message(res))