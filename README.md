# 一个依赖 Graia 的 QQ Bot

```
基于 ieew/miraibot 去除/修改部分功能自用，目前可用的插件会放在另一个仓库里
部分方法名与 ieew/miraibot 有所不同，一些部分有所修改，插件不能无脑通用
```

## 用法
1. 使用 [Mirai Console Loader](https://github.com/iTXTech/mirai-console-loader) 配置好 [mirai](https://github.com/mamoe/mirai)、[mirai-console](https://github.com/mamoe/mirai-console)
2. 在 Mirai Console Loader 的插件目录放入 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 插件并启动 Mirai Console Loader 一次
```
本项目使用 Graia 的版本为 0.19.2，需要使用 mirai-api-http 1
请从 https://github.com/project-mirai/mirai-api-http/releases/tag/v1.12.0 下载 1.12.0 版本的 mirai-api-http
```
3. 修改 mirai-api-http 的配置（设置 AuthKey，开启 WebSocket），再次启动 Mirai Console Loader
4. clone 本项目到新文件夹，cd 进入本项目文件夹内
5. 使用 `pip install -r requirements.txt` 安装依赖的项目
6. 在 config.py 中填写好配置
7. 使用 `python3 run.py` 启动bot

## 插件
[插件仓库 / 示例插件](https://github.com/Redlnn/redbot-plugin)
```
要禁用插件，请重命名插件文件夹或插件文件，请在('_', '!', '.', '#')中任选一个字符加入到文件名最前面
如：
!RollNumber.py
#GetBilibiliVideoInfo.py
.TestPluging
_SearchMinecraftWiki.py
```

## 迁移 miraibot 插件到 redbot
1. 把 `from miraibot import get` 改为 `from miraibot import GetCore`
2. 把 `from miraibot import GraiaMiraiApplication` 改为 `from graia.application.entry import GraiaMiraiApplication`
3. 不兼容 ieew/miraibot 的命令系统，需要自己实现
4. 部分Graia模块要由 `from miraibot import` 改为 `from graia.application.entry`
