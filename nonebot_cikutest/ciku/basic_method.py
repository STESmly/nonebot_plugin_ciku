import os
from nonebot.log import logger
import httpx

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
    
def get_url(url,method='get', headers=None,json=None):
    client = httpx.Client()
    if method == 'get':
        if headers == None:
            res = client.get(url)
        else:
            res = client.get(url, headers=headers)
    elif method == 'post':
        if headers == None:
            if json == None:
                res = client.post(url)
            else:
                res = client.post(url, json=json)
        else:
            if json == None:
                res = client.post(url, headers=headers)
            else:
                res = client.post(url, headers=headers, json=json)
    return res.text