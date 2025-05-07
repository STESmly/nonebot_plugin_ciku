from abc import ABC, abstractmethod
from nonebot.adapters.onebot.v11 import Event
class ParseRule(ABC):
    @abstractmethod
    async def process(self, line: str, event: Event,arg_list:list,async_def_list:list) -> str:
        pass