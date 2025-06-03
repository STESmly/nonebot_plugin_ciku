from .ciku import *
from nonebot import on_message

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="词库进阶版",
    description="词库进阶版",
    usage="写在readme上了",
    type="application",
    homepage="https://github.com/STESmly/nonebot_plugin_nonebot_plugin_ciku",
    config=None,
    supported_adapters={"~onebot.v11"},
)

async def load_group_switches():
    config_file = group_list / "group_switches.json"
        
    if not config_file.exists():
        (bot,) = nonebot.get_bots().values()
        data = await bot.call_api("get_group_list", no_cache=True)
        default_config = {
                    "global_enabled": True,
                    "groups": [
                        {"group_id": g["group_id"], "enabled": True} 
                        for g in data
                    ]
                }
        config_file.write_text(json.dumps(default_config, ensure_ascii=False, indent=2))
    return json.loads(config_file.read_text(encoding="utf-8"))
if not ck_path.exists():
    ck_path.mkdir(parents=True, exist_ok=True)
    open(ck_path / "dicpro.ck", 'w', encoding='utf-8').close()
Group_Message = on_message()

@Group_Message.handle()
async def _(event: GroupMessageEvent):
    config = await load_group_switches()
    groups_dict = {group["group_id"]: group["enabled"] for group in config["groups"]}
    msg = event.original_message
    await push_log(f"[Bot（{event.self_id}）] <- 群聊 [{event.group_id}] | 用户 {event.user_id} : {msg}")
    if config["global_enabled"]:
        await check_input(str(msg), event)
    elif groups_dict.get(event.group_id, False):
        await check_input(str(msg), event)