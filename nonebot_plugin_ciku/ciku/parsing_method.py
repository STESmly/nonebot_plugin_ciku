# parsing_method.py
import nonebot
from .basic_method import read_txt, write_txt
from .parser_rules import ParseRule
import importlib,re
import inspect
import pathlib
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent,MessageSegment,Event,Message

class Parser:
    def __init__(self):
        self.rules: list[ParseRule] = []
        self.load_default_rules()
        self.load_custom_rules()
    
    def load_default_rules(self):
        """加载parser_rules.py中的规则"""
        from . import parser_rules  # 导入默认规则模块
        self._load_rules_from_module(parser_rules)

    def load_custom_rules(self):
        """加载自定义拓展文件夹中的规则"""
        custom_dir = pathlib.Path("自定义拓展")
        if not custom_dir.exists():
            custom_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建 __init__.py 文件并写入内容
            init_file = custom_dir / "__init__.py"
            with open(init_file, 'w', encoding='utf-8') as file:
                file.write("from . import *\n")
            return

        for file_path in custom_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            module_name = file_path.stem
            try:
                spec = importlib.util.spec_from_file_location(
                    f"自定义拓展.{module_name}", file_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.success(f"成功加载自定义规则包: {module_name}")
                self._load_rules_from_module(module)
                
            except Exception as e:
                logger.error(f"加载自定义规则 {file_path} 失败: {e}")

    def _load_rules_from_module(self, module):
        """从模块加载所有ParseRule子类"""
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, ParseRule) and not inspect.isabstract(obj):
                self.register_rule(obj())
                logger.success(f"成功加载规则类: {name}")

    def register_rule(self, rule: ParseRule):
        self.rules.append(rule)
    
    def parse_line(self, line: str, event: Event,tab_time:int,arg_list:list,async_def_list:list) -> str:
        for rule in self.rules:
            if rule.match(line, event,tab_time,arg_list,async_def_list):
                line,tab_time = rule.process(line, event,tab_time, arg_list,async_def_list)
        return line,tab_time

# 初始化解析器时会自动加载规则
parser = Parser()

async def send_input(res_lst, event: Event,arg_list: list,async_def_lst:list):
    finall_res = ''
    async_def_res_list = ""
    tab_time = 0
    for line in res_lst:
        if matches := re.findall(r'^\$回调 ([^\$]*)\$$', line):
            for match_data in matches:
                data = f"ck_res_finall_data += {match_data}()"
                finall_res += line.replace(f'$回调 {match_data}$', data)
                for async_def in async_def_lst:
                    first = async_def.split('\n')[0]
                    async_match = re.match(rf'^\[内部\]{match_data}$', first)
                    if async_match:
                        async_def_res_list = f"""def {match_data}():\n    ck_res_finall_data = ''\n"""
                        for line in async_def.split('\n')[1:]:
                            tab = ''
                            async_tab_time = 1
                            parsed_line,async_tab_time = parser.parse_line(line, event,async_tab_time,arg_list,async_def_lst)
                            symbols = ['=']
                            macth_1 = re.match(r'if .*(==|!=|>=|<=|>|<).*:', parsed_line)
                            macth_2 = re.match(r'for.*in.*:', parsed_line)
                            if macth_1:
                                for time in range(async_tab_time-1):
                                    tab += '    '
                            elif macth_2:
                                for time in range(async_tab_time-1):
                                    tab += '    '
                            else:
                                for time in range(async_tab_time):
                                    tab += '    '
                            if not any(symbol in parsed_line for symbol in symbols) and len(parsed_line) > 0:
                                finall_type = True
                                if macth_1:
                                    finall_type = False
                                if macth_2:
                                    finall_type = False
                                if finall_type:
                                    async_def_res_list += tab + f'ck_res_finall_data += f"{str(parsed_line)}"\n'
                                else:
                                    if len(parsed_line) > 0:
                                        async_def_res_list += tab + parsed_line +'\n'
                                    else:
                                        pass
                            else:
                                if len(parsed_line) > 0:
                                    async_def_res_list += tab + parsed_line +'\n'
                                else:
                                    pass
                        async_def_res_list += "    return ck_res_finall_data\n\n"

        elif matches := re.findall(r'^\$调用 ([^\$]*)\$$', line):
            for match_data in matches:
                for async_def in async_def_lst:
                    first = async_def.split('\n')[0]
                    async_match = re.match(rf'^\[内部\]{match_data}$', first)
                    if async_match:
                        async_def_res_list_send = f"""ck_res_finall_data = ''\n"""
                        for line in async_def.split('\n')[1:]:
                            tab = ''
                            async_tab_time = 0
                            parsed_line,async_tab_time = parser.parse_line(line, event,async_tab_time,arg_list,async_def_lst)
                            symbols = ['=']
                            macth_1 = re.match(r'if .*(==|!=|>=|<=|>|<).*:', parsed_line)
                            macth_2 = re.match(r'for.*in.*:', parsed_line)
                            if macth_1:
                                for time in range(async_tab_time-1):
                                    tab += '    '
                            elif macth_2:
                                for time in range(async_tab_time-1):
                                    tab += '    '
                            else:
                                for time in range(async_tab_time):
                                    tab += '    '
                            if not any(symbol in parsed_line for symbol in symbols) and len(parsed_line) > 0:
                                finall_type = True
                                if macth_1:
                                    finall_type = False
                                if macth_2:
                                    finall_type = False
                                if finall_type:
                                    async_def_res_list_send += tab + f'ck_res_finall_data += f"{str(parsed_line)}"\n'
                                else:
                                    if len(parsed_line) > 0:
                                        async_def_res_list_send += tab + parsed_line +'\n'
                                    else:
                                        pass
                            else:
                                if len(parsed_line) > 0:
                                    async_def_res_list_send += tab + parsed_line +'\n'
                                else:
                                    pass
                    namespace = {
                        'read_txt': read_txt, 
                        'ck_res_finall_data': '',
                        'MessageSegment': MessageSegment,
                        'write_txt': write_txt,
                        'Path': pathlib.Path,
                        }
                    print(async_def_res_list_send)
                    exec(async_def_res_list_send, namespace)
                    res_msg = namespace.get('ck_res_finall_data', None)
                    (bot,) = nonebot.get_bots().values()
                    await bot.send_msg(message_type="group", group_id=event.group_id, message=Message(res_msg))
            
        else:
            tab = ''
            parsed_line,tab_time = parser.parse_line(line, event,tab_time,arg_list,async_def_lst)
            symbols = ['=']
            macth_1 = re.match(r'if .*(==|!=|>=|<=|>|<).*:', parsed_line)
            macth_2 = re.match(r'for.*in.*:', parsed_line)
            if tab_time > 0:
                if macth_1:
                    for time in range(tab_time-1):
                        tab += '    '
                elif macth_2:
                    for time in range(tab_time-1):
                        tab += '    '
                else:
                    for time in range(tab_time):
                        tab += '    '
            if not any(symbol in parsed_line for symbol in symbols) and len(parsed_line) > 0:
                finall_type = True
                if macth_1:
                    finall_type = False
                if macth_2:
                    finall_type = False
                if finall_type:
                    finall_res += tab + f'ck_res_finall_data += f"{str(parsed_line)}"\n'
                else:
                    if len(parsed_line) > 0:
                        finall_res += tab + parsed_line +'\n'
                    else:
                        pass
            else:
                if len(parsed_line) > 0:
                    finall_res += tab + parsed_line +'\n'
                else:
                    pass
    finall_res = async_def_res_list + finall_res
    namespace = {
        'read_txt': read_txt, 
        'ck_res_finall_data': '',
        'MessageSegment': MessageSegment,
        'write_txt': write_txt,
        'Path': pathlib.Path,
        }
    exec(finall_res, namespace)
    return namespace.get('ck_res_finall_data', None)