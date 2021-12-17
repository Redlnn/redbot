<div align="center">

# redbot

一个以 [Graia Ariadne](https://github.com/GraiaProject/Ariadne) 框架为基础的 QQ 机器人

</div>

<p align="center">
<img src="https://img.shields.io/badge/works-for%20me-yellow" alt="works for me" />
<img src="https://img.shields.io/badge/works-on%20my%20machine-green" alt="works on my machine" />
<a href="https://github.com/Redlnn/redbot/blob/master/LICENSE"><img src="https://img.shields.io/github/license/Redlnn/redbot" alt="Licence" /></a>
<a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black" /></a>
<a href="https://pycqa.github.io/isort/"><img src="https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336" alt="Imports: isort" /></a>
</p>

<div align="center">

**本 Bot 的设计只考虑本人需求，因此配置文件格式及部分模块可能会大改，推荐 [`A60(djkcyl)`](https://github.com/djkcyl/) 的 [`ABot`](https://github.com/djkcyl/ABot-Graia/)**

**本仓库偶尔会 Force Push，不建议 Fork**

⇒ **[文件目录结构](./FILES.md)** ⇐

</div>

## 功能列表

- Bot菜单、模块管理及查询
- Bot 版本与系统运行情况查询
- 消息触发支持：全局黑名单控制、成员权限控制、频率限制
- 用你的头像生成点啥
- 自动回复：精确匹配、模糊匹配、正则匹配，支持带图回复
- 吃啥？
- 我的世界服务器管理： 白名单管理、执行命令
- 我的世界服务器 Motd Ping
- 我的世界中文 Wiki 搜索
- 历史聊天数据记录
- 聊天历史词云生成
- BiliBili 视频解析：支持小程序、卡片分享、av号、BV号、B站链接
- 帮你做选择
- 读取被回复消息的<可持久化字符串>及使用<可持久化字符串>发送消息
- 每日抽签（人品检测）：~~狗屁不通的签文生成~~
- 涩图（不可以色色噢）
- 随机数抽取
- 消息内容转图片（支持纯文本和静态图像）

### TODO（咕咕咕？

- [ ] 自动回复使用数据库储存并支持在群内修改回复内容
- [ ] 概率复读
- [ ] 留言提醒
- [ ] 二维码生成
- [ ] BiliBili 动态/直播 订阅推送
- [ ] Pixiv 搜图

## 鸣谢 & 相关项目

> 这些项目也很棒, 可以去他们的项目主页看看, 点个 Star 鼓励他们的开发工作吧

特别感谢 [`Mamoe Technologies`](https://github.com/mamoe) 给我们带来这些精彩的项目:

- [`mirai`](https://github.com/mamoe/mirai) & [`mirai-console`](https://github.com/mamoe/mirai-console): 一个在全平台下运行，提供 QQ Android 和 TIM PC 协议支持的高效率机器人框架
- [`mirai-api-http`](https://github.com/project-mirai/mirai-api-http): 为本项目提供与 mirai 交互方式的 mirai-console 插件

感谢 [`GraiaProject`](https://github.com/GraiaProject) 给我们带来这些项目:

- [`Broadcast Control`](https://github.com/GraiaProject/BroadcastControl): 高性能, 高可扩展性，设计简洁，基于 asyncio 的事件系统
- [`Ariadne`](https://github.com/GraiaProject/Ariadne): 一个设计精巧, 协议实现完备的, 基于 mirai-api-http v2 的即时聊天软件自动化框架
- [`Saya`](https://github.com/GraiaProject/Saya) 简洁的模块管理系统
- [`Scheduler`](https://github.com/GraiaProject/Scheduler): 简洁的基于 `asyncio` 的定时任务实现
- [`Application`](https://github.com/GraiaProject/Application): Ariadne 的前身，一个设计精巧, 协议实现完备的, 基于 mirai-api-http 的即时聊天软件自动化框架

本 QQ 机器人在开发中还参考了如下项目:

- [`ABot`](https://github.com/djkcyl/ABot-Graia/): 一个使用 [Graia-Ariadne](https://github.com/GraiaProject/Ariadne) 搭建的 QQ 功能性~~究极缝合怪~~机器人
- [`Xenon`](https://github.com/McZoo/Xenon): 一个优雅，用户友好的，基于 [mirai](https://github.com/mamoe/mirai) 与 [Graia Project](https://github.com/GraiaProject/) 的 QQ 机器人应用
- [`SereinFish Bot`](https://github.com/coide-SaltedFish/SereinFish)：一个基于 [YuQ](https://github.com/YuQWorks) 的 QQ 机器人
