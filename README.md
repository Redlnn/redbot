<div align="center">

# redbot

一个以 [Graia Ariadne](https://github.com/GraiaProject/Ariadne) 框架为基础的 QQ 机器人

</div>

<p align="center">
  <img src="https://img.shields.io/badge/works-for%20me-yellow" alt="works for me" />
  <img src="https://img.shields.io/badge/works-on%20my%20machine-green" alt="works on my machine" />
  <a href="https://github.com/Redlnn/redbot/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/Redlnn/redbot" alt="Licence" />
  </a>
  <a href="https://github.com/psf/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black" />
  </a>
  <a href="https://pycqa.github.io/isort/">
    <img src="https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336" alt="Imports: isort" />
  </a>
</p>

<p align="center">
  <img src="https://count.getloli.com/get/@Redlnn-redbot?theme=rule34" alt="访问次数" />
</p>

## 注意事项

1. **本仓库经常 Force Push，不建议 Fork 和 Clone**
2. 本 Bot 的设计只考虑本人需求随时可能大改，推荐使用 [`ABot`](https://github.com/djkcyl/ABot-Graia/) 和 [`sagiri-bot`](https://github.com/SAGIRI-kawaii/sagiri-bot)

## 功能列表

- Bot 菜单、模块管理及查询
- Bot 管理
- Bot 版本与系统运行情况查询
- 撤回 Bot 自己最近发的消息
- 吃啥？
- 我的世界服务器 Ping
- 我的世界中文 Wiki 搜索
- BiliBili 视频分享解析：支持小程序、卡片分享、av号、BV号、B站链接
- 别戳我
- 消息转图片（支持纯文本和静态图像）
- 历史聊天数据记录
- 读取被回复消息的<可持久化字符串>及使用<可持久化字符串>发送消息
- 每日抽签（人品检测）：~~狗屁不通的签文生成~~
- 随机数抽取
- 聊天历史词云生成

## 部署

请参阅 [如何部署 redbot](https://github.com/Redlnn/redbot/wiki/%E5%A6%82%E4%BD%95%E9%83%A8%E7%BD%B2-redbot)

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
- [`SereinFish Bot`](https://github.com/coide-SaltedFish/SereinFish)
