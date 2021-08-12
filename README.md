# 一个依赖 Graia 的 QQ Bot

```
基于 ieew/miraibot 去除/修改部分功能自用，目前可用的插件会放在另一个仓库里
部分方法名与 ieew/miraibot 有所不同，一些部分有所修改，插件不能无脑通用
```

## 用法
1. 使用 `pip install -r requirements.txt` 安装依赖的项目
2. 在 config.py 中设置好配置
3. 使用 `python3 run.py` 启动bot

## 插件列表
[插件仓库](https://github.com/Redlnn/redbot-plugin)
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

### 示范插件
详见 [ieew/miraibot](https://github.com/ieew/miraibot)
