import re
from .parsing_method import send_input
from pathlib import Path
from nonebot.adapters.onebot.v11 import GroupMessageEvent,PokeNotifyEvent,Event
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

async def get_async_def():
    file_path = f'dicpro.ck'
    if not os.path.exists(file_path):
        open(file_path, 'w', encoding='utf-8').close()
    with open(file_path,'r', encoding='utf-8') as f:
        txt_res = f.read()
        parts = re.split('\n\n\n|\n\n', txt_res)
        txt_finall_res = [i for i in parts if len(i) > 0]
        res_lst = []
        for i in txt_finall_res:
            first = i.split('\n')[0]
            if len(first) != 0:
                if first not in ['[戳一戳]','[入群申请]']:
                    match = re.match(r'^\[内部\].*$', first)
                    if match:
                        res_lst.append(i)
                    else:
                        pass
                else:
                    pass
            else:
                first = i.split('\n')[1]
                if first not in ['[戳一戳]','[入群申请]']:
                    match = re.match(r'^\[内部\].*$', first)
                    if match:
                        res_lst.append(i)
                    else:
                        pass
                else:
                    pass
        return res_lst

async def check_input(user_input, event : GroupMessageEvent):
    txt_finall_res = await get_text()
    async_def_lst  = await get_async_def()
    for i in txt_finall_res:
        first = i.split('\n')[0]
        if len(first) != 0:
            if first not in ['[戳一戳]','[入群申请]']:
                match = re.match(rf'^{first}$', user_input)
                if match:
                    res_lst = i.split('\n')[1:]
                    arg_lst = list(match.groups())
                    return await send_input(res_lst, event, arg_lst,async_def_lst)
                else:
                    pass
            else:
                pass
        else:
            first = i.split('\n')[1]
            if first not in ['[戳一戳]','[入群申请]']:
                match = re.match(rf'{first}', user_input)
                if match:
                    res_lst = i.split('\n')[2:]
                    arg_lst = list(match.groups())
                    return await send_input(res_lst, event, arg_lst,async_def_lst)
                else:
                    pass
            else:
                pass
    return None

async def system_event_poke_input(event : PokeNotifyEvent):
    txt_finall_res = await get_text()
    async_def_lst  = await get_async_def()
    for i in txt_finall_res:
        first = i.split('\n')[0]
        if len(first) != 0:
            if first == '[戳一戳]':
                res_lst = i.split('\n')[1:]
                arg_lst = None
                return await send_input(res_lst, event, arg_lst,async_def_lst)
            else:
                pass
        else:
            first = i.split('\n')[1]
            if first == '[戳一戳]':
                res_lst = i.split('\n')[2:]
                arg_lst = None
                return await send_input(res_lst, event, arg_lst,async_def_lst)
            else:
                pass
    return None
