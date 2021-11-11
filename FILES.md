# [redbot](https://github.com/Redlnn/redbot) 的主要文件列表

```
redbot  根目录
├── README.md
├── config.py  配置文件
├── data/  数据目录
├── fonts/  字体目录（文本转图片所用）
├── logs/  日志目录
├── modules  插件目录
│   ├── AutoReply/  自动回复
│   ├── MinecraftServerManger/  我的世界服务器管理
│   ├── MinecraftServerPing/  我的世界服务器 Motd Ping
│   ├── BiliVideoInfo.py  BiliBili 视频解析
│   ├── BotStatus.py  Bot版本与系统运行情况查询
│   ├── LogMsgHistory.py  历史聊天数据记录
│   ├── Menu.py  菜单
│   ├── ReadAndSend.py  读取/发送消息的可持久化字符串
│   ├── RenpinChecker.py  每日抽签（人品检测）
│   ├── RollNumber.py  随机数抽取
│   ├── SearchMinecraftWiki.py  我的世界中文 Wiki 搜索
│   └── TextWithImg2Img.py  消息内容转图片
└── utils  通用功能目录
    ├── Database  数据库相关
    │   ├── database.py  数据库初始化（暂时仅作为示例无调用）
    │   └── msg_history.py  聊天历史数据库（记录、查询）
    └── Limit  Bot 事件触发限制相关
        ├── Blacklist.py  群、私聊、临时会话黑名单
        ├── Permission.py  群、私聊、临时会话权限控制
        ├── Rate.py  群、私聊、临时会话调用频率限制
        ├── logger.py  日志管理
        └── TextWithImg2Img  文本（及图片）合成图片
```
