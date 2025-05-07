import re
from pathlib import Path
from nonebot.adapters.onebot.v11 import GroupMessageEvent,PokeNotifyEvent,Event
import os
from .webui import ck_path
from .util import Parsing_parameters
from .lexicon_parser import send_input

directory = ck_path

async def get_text(file_path):
    if not os.path.exists(file_path):
        open(file_path, 'w', encoding='utf-8').close()
    with open(file_path, 'r', encoding='utf-8') as f:
        txt_res = f.read()
        parts = re.split('\n\n\n|\n\n', txt_res)
        txt_finall_res = [i for i in parts if len(i) > 0]
    return txt_finall_res

async def get_async_def(file_path):
    if not os.path.exists(file_path):
        open(file_path, 'w', encoding='utf-8').close()
    with open(file_path, 'r', encoding='utf-8') as f:
        txt_res = f.read()
        parts = re.split('\n\n\n|\n\n', txt_res)
        txt_finall_res = [i for i in parts if len(i) > 0]
        res_lst = []
        for i in txt_finall_res:
            first = i.split('\n')[0]
            if len(first) != 0:
                if first not in ['[戳一戳]', '[入群申请]']:
                    match = re.match(r'^\[内部\].*$', first)
                    if match:
                        res_lst.append(i)
                    else:
                        pass
                else:
                    pass
            else:
                first = i.split('\n')[1]
                if first not in ['[戳一戳]', '[入群申请]']:
                    match = re.match(r'^\[内部\].*$', first)
                    if match:
                        res_lst.append(i[1:])
                    else:
                        pass
                else:
                    pass
        return res_lst

async def check_input(user_input, event: GroupMessageEvent, directory: str = directory):
    try:
        for file_name in os.listdir(directory):
            if file_name.endswith('.ck'):
                file_path = os.path.join(directory, file_name)
                txt_finall_res = await get_text(file_path)
                async_def_lst = await get_async_def(file_path)
                for i in txt_finall_res:
                    first = i.split('\n')[0]
                    if len(first) != 0:
                        if first not in ['[戳一戳]', '[入群申请]']:
                            match = re.match(rf'^{first}$', user_input)
                            if match:
                                res_data = i.split('\n')[1:]
                                res_data = '\n'.join(res_data)
                                arg_lst = list(match.groups())
                                data = Parsing_parameters(args=arg_lst, main_code=res_data, add_call_functions=async_def_lst,bs_event=event)
                                await send_input(data)
                            else:
                                pass
                        else:
                            pass
                    else:
                        first = i.split('\n')[1]
                        if first not in ['[戳一戳]', '[入群申请]']:
                            match = re.match(rf'{first}', user_input)
                            if match:
                                res_data = i.split('\n')[2:]
                                res_data = '\n'.join(res_data)
                                arg_lst = list(match.groups())
                                data = Parsing_parameters(args=arg_lst, main_code=res_data, add_call_functions=async_def_lst,bs_event=event)
                                await send_input(data)
                            else:
                                pass
                        else:
                            pass
    except FileNotFoundError:
        ck_path.mkdir(parents=True, exist_ok=True)
        open(ck_path / "dicpro.ck", 'w', encoding='utf-8').close()
    return None