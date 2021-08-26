# 一个依赖 Graia 的 QQ Bot

基于 ieew/miraibot 去除/修改部分功能自用，目前可用的插件会放在另一个仓库里  
部分方法名与 ieew/miraibot 有所不同，一些部分有所修改，插件不能无脑通用

## 用法
1. 使用 [Mirai Console Loader](https://github.com/iTXTech/mirai-console-loader) 配置好 [mirai](https://github.com/mamoe/mirai)、[mirai-console](https://github.com/mamoe/mirai-console)
2. 在 Mirai Console Loader 的插件目录放入 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 插件并启动 Mirai Console Loader 一次

> 本项目使用经过修改的 0.19.2 版本的 Graia，需要使用 mirai-api-http 1 而不是 2  
> 请从 [这里](https://github.com/project-mirai/mirai-api-http/releases/tag/v1.12.0) 下载 1.12.0 版本的 mirai-api-http  
> 魔改 Graia 步骤：
> 1. pip install graia-application-mirai==0.19.2
> 2. 打开 site-packages/graia/application/group.py，
>    按照 [b16188c](https://github.com/GraiaProject/Application/commit/b16188c9d4bd7c87953beb662e7a9ce202844181) 修改
> 3. 打开 site-packages/graia/application/event/lifecycle.py，
>    把开头的import部分改成如下所示：
```
from typing import Any
from graia.broadcast.entities.event import BaseEvent, BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from pydantic.main import BaseModel
```

3. 修改 mirai-api-http 的配置（设置 AuthKey，开启 WebSocket），再次启动 Mirai Console Loader
4. clone 本项目到新文件夹，cd 进入本项目文件夹内
5. 使用 `pip install -r requirements.txt` 安装依赖
6. 在 config.py 中填写好配置
7. 使用 `python3 run.py` 启动bot

## 插件
__[插件仓库 / 示例插件](https://github.com/Redlnn/redbot-plugin)__  

要禁用插件，请重命名插件文件夹或插件文件  
请在 `('_', '!', '.', '#')` 中任选一个字符加入到文件名最前面例如：
- `!RollNumber.py`
- `#GetBilibiliVideoInfo.py`
- `.TestPluging`
- `_SearchMinecraftWiki.py`


## 迁移 miraibot 插件到 redbot
1. 把 `from miraibot import get` 改为 `from miraibot import GetCore`
2. 部分 Graia 的模块要由 `from miraibot import` 改为 `from graia.application.entry`。  
例如，把 `from miraibot import GraiaMiraiApplication` 改为 `from graia.application.entry import GraiaMiraiApplication`
3. ~~ieew/miraibot 的命令系统暂时不够完善（至少我连启动都没法启动）。暂时去掉了，有需要的话要自己实现~~  
  （目前基于 ieew/miraibot 原有的指令系统修改出了暂时可用的版本，示例插件见[这里](./miraibot/plugins/#group_command_test.py)）
