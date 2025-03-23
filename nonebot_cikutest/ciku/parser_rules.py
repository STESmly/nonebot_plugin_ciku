from abc import ABC, abstractmethod
import re,json,ast
from .basic_method import *
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment

class ParseRule(ABC):
    @abstractmethod
    def match(self, line: str, event: GroupMessageEvent,tab_time:int) -> bool:
        pass

    @abstractmethod
    def process(self, line: str, event: GroupMessageEvent,tab_time:int) -> str:
        pass

class 冒号_rule(ParseRule):
    def match(self, line, event,tab_time):
        return re.search(r'^.*:.*$', line) is not None
    
    def process(self, line, event,tab_time):
        parts = line.split(':', 1)
        stripped_part = parts[1].strip().replace("'", '"')
        try:
            json.loads(stripped_part)
            return f'ck_bianliang_{parts[0]} = {stripped_part}', tab_time
        except json.JSONDecodeError:
            if re.match(r'^如果:(.*) (==|!=|>=|<=|>|<) (.*)$',line):
                return f'{parts[0]} = f"{stripped_part}"', tab_time
            if re.match(r'±.*:.*±',line):
                return line, tab_time
            else:
                return f'ck_bianliang_{parts[0]} = f"{stripped_part}"', tab_time
        
class 变量_rule(ParseRule):
    def match(self, line, event,tab_time):
        return '%' in line

    def process(self, line, event,tab_time):
        variables = re.findall(r'%([^%]*)%', line)
        for var in variables:
            if var == '群号':
                line = line.replace(f'%{var}%', f'{event.group_id}')
            elif var == 'QQ':
                line = line.replace(f'%{var}%', f'{event.user_id}')
            line = line.replace(f'%{var}%', f'{{{"ck_bianliang_"+str(var)}}}')
        return f'{line}',tab_time
    
class 读_1_Rule(ParseRule):
    """读取txt文件"""
    def match(self, line, event,tab_time):
        return re.search(r'\$读 (.*?) (.*?) (.*?)\$', line) is not None

    def process(self, line, event,tab_time):
        matches = re.findall(r'\$读 ([^\$]*) ([^\$]*) ([^\$]*)\$', line)
        if matches:
            for match in matches:
                data = "{read_txt(f'" + match[0] + "', f'" + match[2] + "', f'" + match[1] + "')}"
                line = line.replace(f'$读 {match[0]} {match[1]} {match[2]}$', data)
        return line,tab_time

class 读_2_Rule(ParseRule):
    """读取txt文件"""
    def match(self, line, event,tab_time):
        return re.search(r'\$读 (.*?) (.*?)\$', line) is not None
    
    def process(self, line, event,tab_time):
        matches = re.findall(r'\$读 ([^\$]*) ([^\$]*)\$', line)
        if matches:
            for match in matches:
                data = "{read_txt(f'" + match[0] + "', f'" + match[1] + "')}"
                line = line.replace(f'$读 {match[0]} {match[1]}$', data)
        return line,tab_time
    
class 写_1_Rule(ParseRule):
    """读取txt文件"""
    def match(self, line, event,tab_time):
        return re.search(r'\$写 (.*?) (.*?) (.*?)\$', line) is not None

    def process(self, line, event,tab_time):
        matches = re.findall(r'\$写 ([^\$]*) ([^\$]*) ([^\$]*)\$', line)
        if matches:
            for match in matches:
                data = "{write_txt(f'" + match[0] + "', f'" + match[2] + "', f'" + match[1] + "')}"
                line = line.replace(f'$写 {match[0]} {match[1]} {match[2]}$', data)
        return line,tab_time
    
class 写_2_Rule(ParseRule):
    """读取txt文件"""
    def match(self, line, event,tab_time):
        return re.search(r'\$写 (.*?) (.*?)\$', line) is not None

    def process(self, line, event,tab_time):
        matches = re.findall(r'\$写 ([^\$]*) ([^\$]*)\$', line)
        if matches:
            for match in matches:
                data = "{write_txt(f'" + match[0] + "', f'" + match[1] + "')}"
                line = line.replace(f'$写 {match[0]} {match[1]}$', data)
        return line,tab_time

class 正负_Rule(ParseRule):
    def match(self, line, event,tab_time):
        return '±' in line

    def process(self, line, event,tab_time):
        # 分割文本和指令
        parts = re.split(r'(±.*?±)', line)
        
        for part in parts:
            if not part:
                continue
            if part.startswith('±') and part.endswith('±'):
                content = part[1:-1].strip()
                action_parts = content.split(maxsplit=1)
                if len(action_parts) < 1:
                    continue
                
                action_type = action_parts[0]
                args = action_parts[1] if len(action_parts) > 1 else ''
                if action_type == 'at':
                    data = '{MessageSegment.at(' +args +')}'
                    line = line.replace(f'±{content}±', data)
                if action_type == 'reply':
                    data = '{MessageSegment.reply(' + str(event.message_id) +')}'
                    line = line.replace(f'±{content}±', data)
                if action_type == 'img':
                    url_pattern = re.compile(
                    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                    )
                    if url_pattern.match(args):
                        data = "{MessageSegment.image('" + args +"')}"
                        line = line.replace(f'±{content}±', data)
                    else:
                        if not args[1:2] == ':/':
                            if not args[0:1] == '/':
                                args = '/' + args
                            file_path = os.path.join(os.getcwd()[0:2], args).replace('\\', '/')
                        data = "{MessageSegment.image(Path('" + file_path +"'))}"
                        line = line.replace(f'±{content}±', data)
        return line,tab_time

class 如果_Rule(ParseRule):
    def match(self, line, event,tab_time):
        return re.match(r'^如果 = f"(.*) (==|!=|>=|<=|>|<) (.*)"$',line) or re.match(r'^如果尾$',line)

    def process(self, line, event,tab_time):
        parts = re.match(r'^如果 = f"(.*) (==|!=|>=|<=|>|<) (.*)"$',line)
        parts_match = re.match(r'^如果尾$',line)
        if parts:
            line = 'if ' + parts.group(1) + parts.group(2) + parts.group(3) + ':'
            tab_time += 1
        elif parts_match:
            line = ''
            tab_time -= 1
        return line,tab_time
    
class 数组_Rule(ParseRule):
    """读取txt文件"""
    def match(self, line, event,tab_time):
        return re.search(r'@', line) is not None

    def process(self, line, event,tab_time):
        main_pattern = r'@\{([^}]*)\}((?:\[[^]]*\])+)'
        main_match_data = re.findall(main_pattern, line)


        if main_match_data:
            for main_match in main_match_data:
                name = main_match[0]
                brackets_part = main_match[1]
                
                bracket_contents = re.findall(r'\[([^]]*)\]', brackets_part)
                data = ''
                for bracket_content in bracket_contents:
                    data += f'[{bracket_content}]'
                res = '{' + name + data.replace('"',"'") + '}'
                line = line.replace('@{' + name + '}' + data, res)
        return line,tab_time