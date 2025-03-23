# parsing_method.py
from .basic_method import read_txt, write_txt
from .parser_rules import ParseRule
import importlib,re
import inspect
import pathlib
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent,MessageSegment

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
    
    def parse_line(self, line: str, event: GroupMessageEvent,tab_time:int) -> str:
        for rule in self.rules:
            if rule.match(line, event,tab_time):
                line,tab_time = rule.process(line, event,tab_time)
        return line,tab_time

# 初始化解析器时会自动加载规则
parser = Parser()

async def send_input(res_lst, event: GroupMessageEvent):
    finall_res = ''
    tab_time = 0
    for line in res_lst:
        tab = ''
        parsed_line,tab_time = parser.parse_line(line, event,tab_time)
        symbols = ['=']
        macth = re.match(r'if .*(==|!=|>=|<=|>|<).*:', parsed_line)
        if tab_time > 0:
            if macth:
                for time in range(tab_time-1):
                    tab += '    '
            else:
                for time in range(tab_time):
                    tab += '    '
        if not any(symbol in parsed_line for symbol in symbols) and not macth and len(parsed_line) > 0:
            finall_res += tab + f'ck_res_finall_data += f"{str(parsed_line)}"\n'
        else:
            if len(parsed_line) > 0:
                finall_res += tab + parsed_line +'\n'
            else:
                pass
    
    namespace = {
        'read_txt': read_txt, 
        'ck_res_finall_data': '',
        'MessageSegment': MessageSegment,
        'write_txt': write_txt,
        'Path': pathlib.Path,
        }
    exec(finall_res, namespace)
    return namespace.get('ck_res_finall_data', None)

