from pydantic import BaseModel
from nonebot.adapters.onebot.v11 import Event


class Parsing_parameters(BaseModel):
    args : list[str] = []
    """指令正则过滤后的参数"""
    main_code : str = None
    """指令主代码"""
    add_call_functions : list[str] = []
    """附加调用函数"""
    bs_event: Event = None
    """系统事件"""