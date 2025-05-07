import re
from .util import Parsing_parameters as Rule
import http
import nonebot
from .basic_method import *
from .parser_rules import ParseRule
import importlib,re
import inspect
import pathlib
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent,MessageSegment,Event,Message
from nonebot import require
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store

data_dir = store.get_plugin_data_dir()

ck_path = data_dir / "词库文件"
custom_dir = data_dir / "自定义拓展"
group_list = data_dir / "群列表"
if not group_list.exists():
    group_list.mkdir(parents=True, exist_ok=True)

class Parser:
    def __init__(self):
        self.rules: list[ParseRule] = []
        self.load_default_rules()
        self.load_custom_rules()
    
    def load_default_rules(self):
        """加载parser_rules.py中的规则"""
        from . import basic_rules  # 导入默认规则模块
        self._load_rules_from_module(basic_rules)

    def load_custom_rules(self):
        """加载自定义拓展文件夹中的规则"""
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
    
    async def parse_line(self, line: str, event: Event,arg_list:list,async_def_list:list) -> str:
        for rule in self.rules:
            line,async_def_list = await rule.process(line, event, arg_list,async_def_list)
        return line,async_def_list

# 初始化解析器时会自动加载规则
parser = Parser()