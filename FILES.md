# [redbot](https://github.com/Redlnn/redbot) 的主要文件列表

```
redbot  根目录
├── README.md
├── main.py  Bot 入口
├── config/  配置目录
├── data/  数据目录
├── fonts/  字体目录（文本转图片与词云所用）
├── logs/  日志目录
├── core_modules  核心插件目录
│   ├── module_manage/  Bot 菜单及模块管理
│   ├── bot_manage.py  Bot 管理
│   ├── bot_status.py  Bot版本与系统运行情况查询
│   ├── condole.py  Bot控制台相关功能
│   └── error_handler.py  捕捉Bot运行异常发送给机器人主人
├── modules  插件目录
│   ├── AvatarImgGen/  用你的头像生成点啥
│   ├── EatWhat/  吃啥？
│   ├── MinecraftServerManager/  我的世界服务器管理
│   ├── MinecraftServerPing/  我的世界服务器 Motd Ping
│   ├── BiliVideoInfo.py  BiliBili 视频解析
│   ├── DontNudgeMe.py  别戳我
│   ├── HelpYouChoose  帮你做选择
│   ├── LogMsgHistory.py  历史聊天数据记录
│   ├── MinecraftWikiSearch.py  我的世界中文 Wiki 搜索
│   ├── Msg2Img.py  消息内容转图片
│   ├── ReadAndSend.py  读取/发送消息的可持久化字符串
│   ├── RenpinChecker.py  每日抽签（人品检测）
│   ├── RollNumber.py  随机数抽取
│   ├── Setu.py  涩图（不可以色色噢）
│   └── WordCloud.py 聊天历史词云生成
└── utils  通用功能目录
    ├── control  Bot 触发限制相关
    │   ├── interval.py  群、私聊、临时会话调用频率限制
    │   └── permission.py  群、私聊、临时会话权限及黑名单限制
    ├── database  数据库相关
    │   ├── database.py  初始化数据库及配置文件
    │   └── msg_history.py  聊天历史数据库（记录 & 查询）
    ├── config.py  配置文件加载器
    ├── logger.py  日志管理
    ├── module_register.py  模块信息注册
    ├── path.py  给各模块提供预定义的路径
    └── text2img  带图文本合成图片
```
