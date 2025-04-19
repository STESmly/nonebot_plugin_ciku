from .ciku import *
from nonebot import on_message
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="词库语言进阶版",
    description="模仿手机端框架的词库语言插件，面向懒得学编程的手机框架用户",
    usage="详细见md文档",

    type="application",
    # 发布必填，当前有效类型有：`library`（为其他插件编写提供功能），`application`（向机器人用户提供功能）。

    homepage="https://github.com/STESmly/nonebot_plugin_ciku",
    # 发布必填。

    supported_adapters={"~onebot.v11"},
    # 支持的适配器集合，其中 `~` 在此处代表前缀 `nonebot.adapters.`，其余适配器亦按此格式填写。
    # 若插件可以保证兼容所有适配器（即仅使用基本适配器功能）可不填写，否则应该列出插件支持的适配器。
)

Group_Message = on_message()

@Group_Message.handle()
async def _(event: GroupMessageEvent):
    msg = event.get_message().extract_plain_text()
    res = await check_input(msg, event)
    if res != None:
        await Group_Message.send(Message(res))