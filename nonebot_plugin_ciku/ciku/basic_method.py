import os
from nonebot.log import logger
import httpx
import re
import json

def read_txt(file_path, user_value, user_key=None):
    config = {}
    if not file_path[1:2] == ':/':
        if not file_path[0:1] == '/':
            file_path = '/' + file_path
        file_path = os.path.join(os.getcwd()[0:2], file_path)
    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    if not os.path.exists(file_path):
        open(file_path, 'w', encoding='utf-8').close()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        if user_key != None:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if '=' in line:
                    key, value = line.split('=')
                    config[key.strip()] = value.strip()
                else:
                    logger.warning(f"文件：{file_path} 不符合当前读取逻辑，请检查文件格式")
                    return user_value
            return config.get(user_key, user_value)
            
        else:
            content = f.read()
            if len(content) != 0:
                return content
            else:
                return user_value


def write_txt(file_path, value, key=None):
    if not file_path[1:2] == ':/':
        if not file_path[0:1] == '/':
            file_path = '/' + file_path
        file_path = os.path.join(os.getcwd()[0:2], file_path)

    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    if not os.path.exists(file_path):
        open(file_path, 'w', encoding='utf-8').close()

    config = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        if key != None:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if '=' in line:
                    k, v = line.split('=')
                    config[k.strip()] = v.strip()

                    config[key] = value

                    with open(file_path, 'w', encoding='utf-8') as f:
                        for k, v in config.items():
                            f.write(f"{k} = {v}\n")
                else:
                    logger.warning(f"写入失败！ 文件：{file_path} 不符合当前写入逻辑，请检查文件格式")
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"{value}")
        return ""
    
def get_url(url,method='get', headers=None,upjson=None):
    client = httpx.Client()
    if method == 'get':
        if headers == None or headers == 'None':
            res = client.get(url)
        else:
            res = client.get(url, headers=headers)
    elif method == 'post':
        if headers == None or headers == 'None':
            if upjson == None or upjson == 'None':
                res = client.post(url)
            else:
                res = client.post(url, json=upjson)
        else:
            if upjson == None or upjson == 'None':
                res = client.post(url, headers=headers)
            else:
                res = client.post(url, headers=headers, json=upjson)
    try:
        data = json.loads(res.text)
        return data
    except:
        return res.text


def match_math_expression(expr):
    try:
        json.loads(expr)
        return
    except:
        token_pattern = re.compile(r'\%[^%%]*\%|\[[^\[\]]*\]|\d+|[+\-*/]')

        tokens = token_pattern.findall(expr)
        
        def parse_expression(tokens):
            def parse_term(tokens):
                term = parse_factor(tokens)
                while tokens and tokens[0] in ('*', '/'):
                    tokens.pop(0)  
                    parse_factor(tokens)
                return term

            def parse_factor(tokens):
                if tokens[0] == '(':
                    tokens.pop(0)  
                    parse_expression(tokens)
                    if not tokens or tokens.pop(0) != ')':
                        return
                elif tokens[0] == '[':
                    tokens.pop(0)  
                    parse_bracket_expression(tokens)
                    if not tokens or tokens.pop(0) != ']':
                        return
                else:
                    tokens.pop(0)  
            def parse_bracket_expression(tokens):
                parse_term(tokens)
                while tokens and tokens[0] in ('+', '-'):
                    tokens.pop(0)  
                    parse_term(tokens)

            parse_term(tokens)
            while tokens and tokens[0] in ('+', '-'):
                tokens.pop(0) 
                parse_term(tokens)

        try:
            parse_expression(tokens)
            if tokens:
                return
        except IndexError:
            return 

        return expr.replace('[', '(').replace(']', ')').replace('%', '').replace('{', '(').replace('}', ')')

def list_to_number(list):
    try:
        result = match_math_expression(list)  
    except ValueError as e:
        result = None
    if result is None:
        return False
    return result

def extract_formulas(s):
    """提取所有括号正确闭合的算式块"""
    blocks = []
    current_start = -1
    depth = 0
    for i, c in enumerate(s):
        if c == '[':
            if depth == 0:
                current_start = i 
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0 and current_start != -1:
                blocks.append(s[current_start:i+1]) 
                current_start = -1
    return blocks

def split_formulas(s):
    """将连续表达式分割为独立算式"""
    result = []
    start = 0
    depth = 0
    for i, c in enumerate(s):
        if c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                result.append(s[start:i+1])
                start = i + 1
    if depth != 0:
        raise ValueError(f"括号未闭合: {s}")
    return result

def extract_and_split(s):
    """组合提取和分割过程"""
    blocks = extract_formulas(s)
    final_result = []
    for block in blocks:
        final_result.extend(split_formulas(block))
    return final_result