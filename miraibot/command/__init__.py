from functools import wraps
from .event import MemberPerm

group_commands: dict = {}
friend_commands: dict = {}


def on_command(
    command: str,  # 命令名
    aliases=(),  # 命令别名
    permission=MemberPerm.Member,  # 命令权限
    at=False,  # 是否被 at
    shell_like=False  # 是否使用类 shell 语法
):
    def command_decorator(func):
        @wraps(func)
        async def wrapped_function(*args, **kwargs):
            pass  # 函数调用代码
            return func(*args, **kwargs)
        return wrapped_function
        pass  # 预处理代码
    return command_decorator
