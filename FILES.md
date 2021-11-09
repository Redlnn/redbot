# [redbot](https://github.com/Redlnn/redbot) 的主要文件列表

```
redbot  根目录
├── README.md
├── config.py  配置文件
├── data/  数据目录
├── fonts/  字体目录（文本转图片所用）
├── logs/  日志目录
├── modules  插件目录
│   ├── AutoReply  自动回复
│   ├── MinecraftServerManger  我的世界服务器管理
│   ├── MinecraftServerPing  我的世界服务器 Motd Ping
│   ├── BiliVideoInfo  BiliBili 视频解析
│   ├── Menu  菜单
│   ├── RenpinChecker  每日抽签（人品检测）
│   ├── RollNumber  随机数抽取
│   ├── SearchMinecraftWiki  我的世界中文 Wiki 搜索
│   └── TextWithImg2Img  消息内容转图片
└── utils  通用功能目录
    ├── Database  数据库相关
    │   ├── database.py  数据库初始化（暂时无调用作为示例）
    │   └── msglog.py  聊天历史记录（TODO）
    └── Limit  Bot 事件触发限制相关
        ├── Blacklist.py  群、私聊、临时会话黑名单
        ├── Permission.py  群、私聊、临时会话权限控制
        ├── Rate.py  群、私聊、临时会话调用频率限制
        ├── logger.py  日志管理
        └── TextWithImg2Img  文本（及图片）合成图片
```
