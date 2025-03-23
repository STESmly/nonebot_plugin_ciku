<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-ciku

_✨ NoneBot 插件描述 ✨_

这是一个 onebot.v11的词库插件
</div>

## 📖 介绍

词库插件方面：

面向小白的词库插件,目的是减少编写代码的时间和难度 特点:语言精简 无需重启nb和reload即可实
现功能热重载 缺点:目前仅能实现一些简单的逻辑运行,但随着更新肯定会慢慢削减

支持导入自定义规则

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot_plugin_ciku

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot_plugin_ciku
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_ciku"]

</details>

## ⚙️ 说明

词库文件(dicpro.ck)和自定义拓展文件夹都会在初次使用时自动创建

项目还在持续优化，目前只能就行指令完全匹配，暂时不支持正则语法

<details open>
<summary>变量大全</summary>
目前支持的变量:

| 变量 | 说明 |
|:-----:|:----:|
| %QQ% | 用户id |
| %群号% | 群号 |
| \$读 路径 键 默认值\$ | 读文件 |
| \$写 路径 键 值\$ | 写文件 |
| ±at QQ号± | 艾特用户 |
| ±img 路径/链接± | 发送图片 |
| ±reply 0± | 回复指令消息 |
| @%a%['data'] | 比如你前面写了a:{'data':1},那么为1 |

</details>

## 🎉 使用
### 词库格式
```bash
测试
路径:/词库项目/qrbot/src/plugins/词库v2/
name:['123']
a:$读 %路径%send.txt a 0$
b:$读 %路径%send.txt b 0$
c:$读 %路径%send.txt c 123$
d:±img bug.png±
$写 %路径%send.txt c 哈哈哈$
±reply 0±
%a%《隔断》%b%%c%\n±at %QQ%±\n456789
±img https://homdgcat.wiki/images/emote/Yunli/1.png±
%d%
如果:1 > 2
$读 %路径%send.txt c wdnmd$
如果:%a% == %a%
变量测试成功@%name%[0]
如果尾
如果尾
如果:%a% == %a%
缩进测试成功



测试json
name:['123']
data:{'a':'123','b':'456'}
@%name%[0]\n
@%data%['b']

hello
hi
```

### 自定义拓展

在机器人项目目录下找到《自定义拓展》文件夹
创建py文件，这里是示例

```bash
# example.py

from nonebot import require

require("nonebot_plugin_ciku")

from nonebot_plugin_ciku.ciku.parser_rules import ParseRule

class EmojiRule(ParseRule):
    """示例第三方规则：替换表情符号"""
    
    def match(self, line, event, tab_time) -> bool:
        return re.search(r'#\w+#', line) is not None
    
    def process(self, line, event, tab_time) -> str:
        line = line.replace('#smile#', '😊')
        line = line.replace('#angry#', '😠')
        return f'{line}', tab_time

```