from .parser_rules import *
from .rule_load import *
from .util import Parsing_parameters as psp

def extract_indentation(text):
    original_length = len(text)
    stripped_length = len(text.lstrip())
    indentation_length = original_length - stripped_length
    return text[:indentation_length]

async def send_input(data_lst:psp):
    async_main_code = "async def ck_main_code(event):\n"
    async_call_fuctions = ""
    main_code, call_fuctions = await parser.parse_line(data_lst.main_code, data_lst.bs_event,data_lst.args,data_lst.add_call_functions)
    main_code = 'ck_res_finall_data = ""\n(bot,) = nonebot.get_bots().values()\n' + main_code
    main_code_list = main_code.split('\n')
    for i, line in enumerate(main_code_list):
        ##可做成拓展配置项
        base_match = re.match(r'^\s*ck_bianliang_.*$', line)
        macth_1 = re.match(r'\s*if .*(==|!=|>=|<=|>|<).*:', line)
        macth_2 = re.match(r'\s*for.*in.*:', line)
        if not base_match and len(line) > 0:
            finall_type = True
            if macth_1:
                finall_type = False
            if macth_2:
                finall_type = False
            if finall_type:
                if re.match(r'\s*ck_res_finall_data.*', line):
                    pass
                elif re.match(r'\s*\(bot,\) = nonebot.get_bots\(\).values\(\)', line):
                    pass
                elif re.match(r'\s*await bot.call_api.*', line):
                    pass
                elif re.match(r'\s*await bot.send.*',line):
                    pass
                else:
                    indent = extract_indentation(str(line))
                    res_line = line.replace(indent, '')
                    line = line.replace(str(line),f'{indent}ck_res_finall_data += f"{str(res_line)}"')
            else:
                pass
        else:
            pass
        main_code_list[i] = '    ' + line
    main_code = '\n'.join(main_code_list) + '\n    await bot.send(event, Message(ck_res_finall_data))'
    async_main_code += main_code
    for i, line_list in enumerate(call_fuctions):
        fc_lists = line_list.split('\n')
        call_name = fc_lists[0]
        call_code = fc_lists[1:]
        if matches := re.match(r'^\[内部\](.*)$', call_name):
            call_name = f'async def ck_call_{matches.group(1)}(event):\n    ck_res_finall_data = ""\n    (bot,) = nonebot.get_bots().values()\n'
        for i, line in enumerate(call_code):
            base_match = re.match(r'^\s*ck_bianliang_.*$', line)
            macth_1 = re.match(r'if .*(==|!=|>=|<=|>|<).*:', line)
            macth_2 = re.match(r'for.*in.*:', line)
            if not base_match and len(line) > 0:
                finall_type = True
                if macth_1:
                    finall_type = False
                if macth_2:
                    finall_type = False
                if finall_type:
                    if re.match(r'ck_res_finall_data.*', line):
                        pass
                    elif re.match(r'\(bot,\) = nonebot.get_bots\(\).values\(\)', line):
                        pass
                    elif re.match(r'await bot.call_api.*', line):
                        pass
                    elif re.match(r'await bot.send.*',line):
                        pass
                    else:
                        indent = extract_indentation(str(line))
                        res_line = line.replace(indent, '')
                        line = line.replace(str(line),f'{indent}ck_res_finall_data += f"{str(res_line)}"')
                else:
                    pass
            else:
                pass
            call_code[i] = '    ' + line
        call_code = '\n'.join(call_code) + '\n    return ck_res_finall_data\n\n'
        async_call_fuctions += call_name + call_code
    res_code = async_call_fuctions + '\n' + async_main_code
    print(res_code)

    import_list = {
        'nonebot':nonebot,
        'read_txt': read_txt, 
        'MessageSegment': MessageSegment,
        'write_txt': write_txt,
        'Path': pathlib.Path,
        'get_url': get_url,
        'json':json,
        'Message':Message,
    }
    namespace = import_list.copy()
    exec(res_code, namespace, namespace)
    await namespace['ck_main_code'](data_lst.bs_event)
