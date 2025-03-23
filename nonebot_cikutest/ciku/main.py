import re
from .parsing_method import send_input
from pathlib import Path
from nonebot.adapters.onebot.v11 import GroupMessageEvent
import os


async def get_text():
    file_path = f'dicpro.ck'
    if not os.path.exists(file_path):
        open(file_path, 'w', encoding='utf-8').close()
    with open(file_path,'r', encoding='utf-8') as f:
        txt_res = f.read()
        parts = re.split('\n\n\n|\n\n', txt_res)
        txt_finall_res = [i for i in parts if len(i) > 0]
    return txt_finall_res

async def check_input(user_input, event : GroupMessageEvent):
    txt_finall_res = await get_text()
    for i in txt_finall_res:
        first = i.split('\n')[0]
        if len(first) != 0:
            if user_input == first:
                res_lst = i.split('\n')[1:]
                return await send_input(res_lst, event)
            else:
                pass
        else:
            first = i.split('\n')[1]
            if user_input == first:
                res_lst = i.split('\n')[2:]
                return await send_input(res_lst, event)
            else:
                pass
    return None
