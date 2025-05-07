from .parser_rules import ParseRule
import re,json
from .basic_method import *


class 冒号_rule(ParseRule):
    async def process(self, def_list, event, arg_list, async_def_list):

        def process_line(lines,self_line):
            for i, line in enumerate(lines):
                if re.search(r'^.*:.*$', line) is not None:
                    parts = line.split(':', 1)
                    stripped_part = parts[1].strip().replace("'", '"')
                    if f'%{parts[0]}%' in self_line:
                        try:
                            json.loads(stripped_part)
                            lines[i] = f'ck_bianliang_{parts[0]} = {stripped_part}'
                        except json.JSONDecodeError:
                            if re.match(r'^.*:\$访问[^$]*\$$', line):
                                lines[i] = f'ck_bianliang_{parts[0]} = {stripped_part}'
                            elif re.match(r'^.*:\[.*\]$', line):
                                if '%' in stripped_part:
                                    variables = re.findall(r'%([^%]*)%', stripped_part)
                                    for var in variables:
                                        stripped_part = stripped_part.replace(f'%{var}%', "ck_bianliang_"+str(var))
                                stripped_part = list_to_number(stripped_part)
                                if stripped_part is not False:
                                    lines[i] = f'ck_bianliang_{parts[0]} = {stripped_part}'
                                else:
                                    lines[i] = f'ck_bianliang_{parts[0]} = f"{stripped_part}"'
                            else:
                                lines[i] = f'ck_bianliang_{parts[0]} = f"{stripped_part}"'
                    else:
                        lines[i] = line
            return lines
        if re.search(r'.*:.*', def_list) is not None:
            def_list_lines = def_list.split('\n')
            def_list_lines = process_line(def_list_lines,def_list)
            def_list = '\n'.join(def_list_lines)
        else:
            pass
        for a, async_def_list_line in enumerate(async_def_list):
            if re.search(r'\n.*:.*\n', async_def_list_line) is not None:
                async_list = async_def_list_line.split('\n')
                async_def_list_lines = async_list[1:]
                async_def_list_lines = process_line(async_def_list_lines,async_def_list_line)
                async_def_list_line = async_list[0]+'\n' + '\n'.join(async_def_list_lines)
            else:
                pass
            async_def_list[a] = async_def_list_line
        return def_list,async_def_list
    
class 变量_rule(ParseRule):
    async def process(self, def_list, event, arg_list, async_def_list):

        def process_line(lines):
            if '%' in lines:
                variables = re.findall(r'%([^%]*)%', lines)
                for var in variables:
                    if var == '群号':
                        lines = lines.replace(f'%{var}%', f'{event.group_id}')
                    elif var == 'QQ':
                        lines = lines.replace(f'%{var}%', f'{event.user_id}')
                    elif var == 'BotQQ':
                        lines = lines.replace(f'%{var}%', f'{event.self_id}')
                    elif var == 'TargetQQ':
                        lines = lines.replace(f'%{var}%', f'{event.target_id}')
                    elif match := re.match(r'^括号(\d+)$', var):
                        lines = lines.replace(f'%{var}%', f'{arg_list[int(match.group(1))]}')
                    elif match := re.match(r'^AT(\d+)$', var):
                        if len(at := event.original_message.include("at")) > 0:
                            id = at[int(match.group(1))].data["qq"]
                            lines = lines.replace(f'%{var}%', f'{id}')
                    elif f'ck_bianliang_{var}' in lines:
                        lines = lines.replace(f'%{var}%', f'{{{"ck_bianliang_"+str(var)}}}')
                    else:
                        pass
            return lines
        def_list = process_line(def_list)
        for i, line in enumerate(async_def_list):
            async_def_list[i] = process_line(line)
        return def_list,async_def_list
    
class 数据计算_rule(ParseRule):

    async def process(self, def_list, event, arg_list, async_def_list):
        def process_line(lines,self_list):
            for i, line in enumerate(lines):
                if re.search(r'\[.*\]', self_list) is not None:
                    if not re.search(r'@.*ck_bianliang_.*\[.*\]', line):
                        data = extract_and_split(line)
                        for value in data:
                            stripped_part = list_to_number(value)
                            if stripped_part is not False:
                                line = line.replace(f'{value}', f'{{{stripped_part}}}')
                            else:
                                pass
                    else:
                        pass
                lines[i] = line
            return lines
        
        def_list_lines = def_list.split('\n')
        def_list = '\n'.join(process_line(def_list_lines, def_list))
        for a, async_def_list_line in enumerate(async_def_list):
            async_list = async_def_list_line.split('\n')
            async_def_list_lines = async_list[1:]
            async_def_list_line = async_list[0] + '\n' + '\n'.join(process_line(async_def_list_lines, async_def_list_line))
            async_def_list[a] = async_def_list_line
        return def_list, async_def_list
    
class 读_Rule(ParseRule):
    """读取txt文件"""
    async def process(self, def_list, event, arg_list, async_def_list):
        def process_line(lines):
            matches_3 = re.findall(r'\$读 ([^\$]*) ([^\$]*) ([^\$]*)\$', lines)
            matches_2 = re.findall(r'\$读 ([^\$]*) ([^\$]*)\$', lines)
            if matches_3:
                for match in matches_3:
                    data = "{read_txt(f'" + match[0] + "', f'" + match[2] + "', f'" + match[1] + "')}"
                    lines = lines.replace(f'$读 {match[0]} {match[1]} {match[2]}$', data)
            elif matches_2:
                for match in matches_2:
                    data = "{read_txt(f'" + match[0] + "', f'" + match[1] + "')}"
                    lines = lines.replace(f'$读 {match[0]} {match[1]}$', data)
            return lines
        if re.search(r'\$读 (.*?) (.*?) (.*?)\$', def_list) is not None or \
            re.search(r'\$读 (.*?) (.*?)\$', def_list) is not None:
            def_list = process_line(def_list)
        for i, line in enumerate(async_def_list):
            if re.search(r'\$读 (.*?) (.*?) (.*?)\$', line) is not None or \
                re.search(r'\$读 (.*?) (.*?)\$', line) is not None:
                async_def_list[i] = process_line(line)
        return def_list, async_def_list
    
class 写_Rule(ParseRule):
    """写txt文件"""
    async def process(self, def_list, event, arg_list, async_def_list):
        def process_line(lines):
            matches_3 = re.findall(r'\$写 ([^\$]*) ([^\$]*) ([^\$]*)\$', lines)
            matches_2 = re.findall(r'\$写 ([^\$]*) ([^\$]*)\$', lines)
            if matches_3:
                for match in matches_3:
                    data = "{write_txt(f'" + match[0] + "', f'" + match[2] + "', f'" + match[1] + "')}"
                    lines = lines.replace(f'$写 {match[0]} {match[1]} {match[2]}$', data)
            elif matches_2:
                for match in matches_2:
                    data = "{write_txt(f'" + match[0] + "', f'" + match[1] + "')}"
                    lines = lines.replace(f'$写 {match[0]} {match[1]}$', data)
            return lines
        if re.search(r'\$写 (.*?) (.*?) (.*?)\$', def_list) is not None or \
            re.search(r'\$写 (.*?) (.*?)\$', def_list) is not None:
            def_list = process_line(def_list)
        for i, line in enumerate(async_def_list):
            if re.search(r'\$写 (.*?) (.*?) (.*?)\$', line) is not None or \
                re.search(r'\$写 (.*?) (.*?)\$', line) is not None:
                async_def_list[i] = process_line(line)
        return def_list, async_def_list
    

class 访问_Rule(ParseRule):

    async def process(self, def_list, event, arg_list, async_def_list):
        def process_line(line):
            matches_1 = re.findall(r'\$访问 ([^\$]*)\$', line)
            matches_2 = re.findall(r'\$访问 ([^\$]*) ([^\$]*)\$', line)
            matches_3 = re.findall(r'\$访问 ([^\$]*) ([^\$]*) ([^\$]*)\$', line)
            matches_4 = re.findall(r'\$访问 post ([^\$]*) ([^\$]*) ([^\$]*)\$', line)
            if matches_1:
                for match in matches_1:
                    data = "get_url(f'" + match + "')"
                    line = line.replace(f'$访问 {match}$', data)
            elif matches_2:
                for match in matches_2:
                    data = "get_url(f'" + match[0] + "',get, f'" + match[1] + "',None)"
                    line = line.replace(f'$访问 {match[0]} {match[1]}$', data)
            elif matches_3:
                for match in matches_3:
                    data = "get_url(f'" + match[1] + "',f'" + match[0] + "', headers=f'" + match[2] + "',None)"
                    line = line.replace(f'$访问 {match[0]} {match[1]} {match[2]}$', data)
            elif matches_4:
                for match in matches_4:
                    data = "get_url(f'" + match[0] + "',post, f'" + match[1] + "',f'" + match[2] + "')"
                    line = line.replace(f'$访问 post {match[0]} {match[1]} {match[2]}$', data)
            return line
        if re.search(r'\$访问 (.*?)\$', def_list) is not None or \
            re.search(r'\$访问 (.*?) (.*?)\$', def_list) is not None or \
            re.search(r'\$访问 (.*?) (.*?) (.*?)\$', def_list) is not None or \
            re.search(r'\$访问 post (.*?) (.*?) (.*?)\$', def_list) is not None:
            def_list = process_line(def_list)
        for i,line in enumerate(async_def_list):
            if re.search(r'\$访问 (.*?)\$', line) is not None or \
                re.search(r'\$访问 (.*?) (.*?)\$', line) is not None or \
                re.search(r'\$访问 (.*?) (.*?) (.*?)\$', line) is not None or \
                re.search(r'\$访问 post (.*?) (.*?) (.*?)\$', line) is not None:
                async_def_list[i] = process_line(line)
        return def_list,async_def_list
    
class 数组_Rule(ParseRule):

    async def process(self, def_list, event, arg_list, async_def_list):
        def process_line(line):
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
                    res = '{' + name  + data.replace('"',"'") + '}'
                    line = line.replace('@{' + name + '}' + data, res)
            return line
        if re.search(r'@', def_list) is not None:
            def_list = process_line(def_list)
        for i, line in enumerate(async_def_list):
            if re.search(r'@', def_list) is not None:
                async_def_list[i] = process_line(line)
        return def_list,async_def_list
    

class 正负_Rule(ParseRule):

    async def process(self, def_list, event, arg_list, async_def_list):
        def process_line(line):
            if '±' in line:
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
                        '''if action_type == 'g_poke':
                            data = "await bot.call_api('group_poke',group_id=" + str(event.group_id)+",user_id=" +str(event.user_id)+")"
                            line = line.replace(f'±{content}±', data)'''
            return line
        def_list = process_line(def_list)
        for i,line in enumerate(async_def_list):
            async_def_list[i] = process_line(line)
        return def_list,async_def_list
    
class 如果_Rule(ParseRule):

    async def process(self, def_list, event, arg_list, async_def_list):
        tab_time=0
        def process_line(lines):
            tab_time=0
            for i,line in enumerate(lines):
                parts = re.match(r'^如果:(.*) (==|!=|>=|<=|>|<) (.*)$',line)
                parts_match = re.match(r'^如果尾$',line)
                if parts:
                    line ='\t' * tab_time + 'if ' + parts.group(1) + parts.group(2) + parts.group(3) + ':'
                    tab_time += 1
                elif parts_match:
                    line = ''
                    tab_time -= 1
                else:
                    line = '\t' * tab_time + line
                lines[i] = line
            lines = '\n'.join(lines)
            return lines
        def_list = process_line(def_list.split('\n'))
        for i,line in enumerate(async_def_list):
            async_def_list[i] = process_line(line.split('\n'))
    
        return def_list,async_def_list
    
class 循环_Rule(ParseRule):

    async def process(self, def_list, event, arg_list, async_def_list):
        def process_line(lines):
            tab_time=0
            for i,line in enumerate(lines):
                parts = re.match(r'^循环:(.*) in (.*)$',line)
                parts_match = re.match(r'^循环尾$',line)
                parts_break = re.match(r'^阻断$',line)
                if parts:
                    parts_bianliang = re.match(r'^{.*}$',parts.group(1))
                    if parts_bianliang:
                        line = '\t' * tab_time + 'for ' + parts.group(1).replace('{','').replace('}','') + ' in ' + f'range({parts.group(2)})' + ':'
                        tab_time += 1
                    else:
                        line = '\t' * tab_time + 'for ' + parts.group(1) + ' in ' + parts.group(2) + ':'
                        tab_time += 1
                elif parts_match:
                    line = ''
                    tab_time -= 1
                elif parts_break:
                    line = '\t' * tab_time + 'break'
                    tab_time -= 1
                else:
                    line = '\t' * tab_time + line
                lines[i] = line
            lines = '\n'.join(lines)
            return lines
        def_list = process_line(def_list.split('\n'))
        for i,line in enumerate(async_def_list):
            async_def_list[i] = process_line(line.split('\n'))
        
        return def_list,async_def_list
    
class 调用_Rlue(ParseRule):
    async def process(self, def_list, event, arg_list, async_def_list):
        def process_line(lines):
            matches_retrun = re.findall(r'\$回调 ([^\$]*)\$', lines)
            matches_await = re.findall(r'\$调用 ([^\$]*)\$', lines)
            if matches_retrun:
                for match in matches_retrun:
                    data = f"ck_res_finall_data += await ck_call_{match}(event)"
                    return_type = False
                    for i,line in enumerate(async_def_list):
                        if f"[内部]{match}" in line:
                            return_type = True
                    if return_type == True:
                        lines = lines.replace(f'$回调 {match}$', data)
                    else:
                        lines = lines.replace(f'$回调 {match}$', "")
            if matches_await:
                for match in matches_await:
                    data = f"await bot.send(event, Message(await ck_call_{match}(event)))"
                    await_type = False
                    for i,line in enumerate(async_def_list):
                        if f"[内部]{match}" in line:
                            await_type = True
                    if await_type == True:
                        lines = lines.replace(f'$调用 {match}$', data)
                    else:
                        lines = lines.replace(f'$调用 {match}$', "")
            return lines
        def_list = process_line(def_list)
        for i,line in enumerate(async_def_list):
            async_def_list[i] = process_line(line)
        return def_list,async_def_list