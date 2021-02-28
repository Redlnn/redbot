from functools import wraps

group_commands: dict = {}
friend_commands: dict = {}


def on_command(command: str):
    def command_decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            pass  # 函数调用代码
            return func(args, **kwargs)
        return wrapped_function
    return command_decorator
