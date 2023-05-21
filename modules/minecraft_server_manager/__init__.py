import time
from datetime import datetime

from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.event.mirai import (
    MemberJoinEvent,
    MemberLeaveEventKick,
    MemberLeaveEventQuit,
)
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain, Source
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    SpacePolicy,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member, MemberInfo, MemberPerm
from graia.saya import Channel, Saya
from graiax.shortcut.interrupt import FunctionWaiter
from graiax.shortcut.saya import decorate, dispatch, listen
from loguru import logger
from sqlalchemy.sql import func, select

from libs import db
from libs.control import require_disable
from libs.control.permission import GroupPermission
from libs.text2img import md2img

from .config import config as module_config
from .model import BannedQQList, Player
from .rcon import execute_command
from .utils import is_mc_id, is_uuid
from .whitelist.append import add_whitelist_to_qq
from .whitelist.delete import (
    del_whitelist_by_id,
    del_whitelist_by_qq,
    del_whitelist_by_uuid,
)
from .whitelist.query import (
    gen_query_info_text,
    query_player_by_qq,
    query_player_by_uuid,
    query_uuid_by_qq,
    query_whitelist_by_id,
    query_whitelist_by_uuid,
)

saya = Saya.current()
channel = Channel.current()

channel.meta['name'] = '我的世界服务器管理'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '（自用，仅特殊群启用）提供白名单管理、在线列表查询、服务器命令执行功能\n用法：\n  [!！.]mc'

menu = (
    '## 服务器管理菜单\n'
    '- [!！.]myid <mc正版id> —— 自助申请白名单\n'
    '- [!！.]list —— 获取服务器在线列表\n'
    '- [!！.]wl —— 白名单相关的菜单\n'
    '- [!！.]run <command> —— 【管理】执行服务器命令\n'
    '- [!！.]ban <QQ号或@QQ> [原因] —— 【管理】从服务器封禁一个QQ及其账号\n'
    '- [!！.]pardon <QQ号或@QQ> —— 【管理】将一个QQ从黑名单中移出\n'
    '- [!！.]clear_leave_time ——【管理】从数据库中清除一个QQ的退群时间'
)

wl_menu = (
    '## 白名单管理菜单\n'
    '- [!！.]wl add <QQ号或@QQ> <游戏ID> —— 【管理】为某个ID绑定QQ并给予白名单\n'
    '- [!！.]wl del @QQ —— 【管理】删除某个QQ的所有白名单\n'
    '- [!！.]wl del qq <QQ号> —— 【管理】删除某个QQ的所有白名单\n'
    '- [!！.]wl del id <游戏ID> —— 【管理】删除某个ID的白名单\n'
    '- [!！.]wl del uuid <游戏ID> —— 【管理】删除某个UUID的白名单\n'
    '- [!！.]wl info <@QQ或游戏ID> —— 查询被@QQ或某个ID的信息\n'
    '- [!！.]wl info qq <QQ号> —— 查询某个QQ的信息\n'
    '- [!！.]wl info id <游戏ID> —— 查询某个ID的信息\n'
    '- [!！.]wl clear —— 【管理】清空数据库中的白名单信息（服务器端请自行处理）'
)

menu_img_bytes: bytes
wl_menu_img_bytes: bytes

is_init: bool = False


# ---------------------------------------------------------------------------------------------------------------------


@listen(ApplicationLaunched)
@decorate(require_disable(channel.module))
async def init(app: Ariadne):
    global is_init, menu_img_bytes, wl_menu_img_bytes
    group_list = await app.get_group_list()
    groups = [group.id for group in group_list]
    for group in module_config.activeGroups:
        if group not in groups:
            logger.error(f'要启用mc服务器管理的群组 {group} 不在机器人账号已加入的群组中，自动禁用')
            saya.uninstall_channel(channel)
            return
    result = (await db.exec(func.count(Player.id))).scalar()
    if result == 0:
        logger.info('初始化mc服务器管理数据库中...')
        member_list = await app.get_member_list(module_config.serverGroup)
        data = [
            Player(
                qq=member.id,
                joinTime=(member.join_timestamp * 1000) if member.join_timestamp else None,
                hadWhitelist=False,
            )
            for member in member_list
        ]
        if await db.add_many(data):
            logger.info('mc服务器管理数据库初始化完成')
        else:
            logger.error('mc服务器管理数据库初始化失败')
            raise ValueError('mc服务器管理数据库初始化失败')
    menu_img_bytes = await md2img(menu)
    wl_menu_img_bytes = await md2img(wl_menu)
    is_init = True


# ---------------------------------------------------------------------------------------------------------------------


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]mc')))
@decorate(GroupPermission.require())
async def main_menu(app: Ariadne, group: Group):
    global menu_img_bytes
    if not is_init or group.id not in module_config.activeGroups:
        return
    await app.send_message(group, MessageChain(Image(data_bytes=menu_img_bytes)))


# ---------------------------------------------------------------------------------------------------------------------


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]wl')))
@decorate(GroupPermission.require())
async def whitelist_menu(app: Ariadne, group: Group, message: MessageChain):
    global wl_menu_img_bytes
    if not is_init or group.id not in module_config.activeGroups:
        return
    if len(str(message)[1:]) == 2:
        await app.send_message(group, MessageChain(Image(data_bytes=wl_menu_img_bytes)))


# ---------------------------------------------------------------------------------------------------------------------


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]wl add').space(SpacePolicy.FORCE), WildcardMatch()))
@decorate(GroupPermission.require(MemberPerm.Administrator))
async def add_whitelist(app: Ariadne, group: Group, source: Source, message: MessageChain):
    if not is_init:
        await app.send_message(group, MessageChain(Plain('数据库初始化中，请稍后再试...')))
        return
    elif group.id not in module_config.activeGroups:
        return
    msg = message.split(' ')
    if len(msg) != 4:
        await app.send_message(group, MessageChain(Plain('无效的命令')), quote=source)
        return

    if msg[2].only(Plain) and str(msg[2]).isdigit():
        target = int(str(msg[2]))
    elif msg[2].only(At):
        target = msg[2].get_first(At).target
    else:
        await app.send_message(group, MessageChain(Plain('目标用户不是有效的 QQ 号或 at 对象')), quote=source)
        return

    mc_id = str(msg[3])
    if not msg[3].only(Plain) or not await is_mc_id(mc_id):
        await app.send_message(group, MessageChain(Plain('目标 ID 不是有效的 Minecraft 正版ID')), quote=source)
        return

    await app.send_message(group, (await add_whitelist_to_qq(target, mc_id, True))[0], quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch('[!！.]wl del').space(SpacePolicy.FORCE), WildcardMatch()))
@decorate(GroupPermission.require(MemberPerm.Administrator))
async def del_whitelist(app: Ariadne, group: Group, source: Source, message: MessageChain):
    if not is_init or group.id not in module_config.activeGroups:
        return
    msg = message.split(' ')

    match len(msg):
        case 3:
            if msg[2].only(At):
                target = msg[2].get_first(At).target
                await app.send_message(group, await del_whitelist_by_qq(target), quote=source)
                return
        case 4:
            if msg[2].only(Plain):
                func = str(msg[2])
                if func == 'qq':
                    if msg[3].only(At):
                        target = msg[3].get_first(At).target
                        await app.send_message(group, await del_whitelist_by_qq(target), quote=source)
                        return
                    elif msg[3].only(Plain):
                        target = str(msg[3])
                        if target.isdigit():
                            await app.send_message(group, await del_whitelist_by_qq(int(target)), quote=source)
                        else:
                            await app.send_message(group, MessageChain(Plain('无效的 QQ 号')), quote=source)
                        return
                elif func == 'id' and msg[3].only(Plain):
                    target = str(msg[3])
                    if await is_mc_id(target):
                        await app.send_message(group, await del_whitelist_by_id(target), quote=source)
                    else:
                        await app.send_message(group, MessageChain(Plain('目标 ID 不是有效的 Minecraft 正版ID')), quote=source)
                    return
                elif func == 'uuid' and msg[3].only(Plain):
                    target = str(msg[3])
                    if _ := (await is_uuid(target)):
                        await app.send_message(group, await del_whitelist_by_uuid(_), quote=source)
                    else:
                        await app.send_message(group, MessageChain(Plain('目标不是有效的 UUID')), quote=source)
                    return

    await app.send_message(group, MessageChain(Plain('参数错误，无效的命令')), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


async def t(app: Ariadne, group: Group, source: Source, target: int):
    uuid_list = await query_uuid_by_qq(target)
    if uuid_list is None:
        await app.send_message(group, MessageChain(At(target), Plain(' 好像一个白名单都没有呢~')), quote=source)
        return
    player = await query_player_by_uuid(uuid_list[0].uuid)
    if player is None:
        await app.send_message(group, MessageChain(Plain('没有使用该 ID 的 QQ')), quote=source)
    else:
        await app.send_message(group, await gen_query_info_text(player), quote=source)


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]wl info').space(SpacePolicy.FORCE), WildcardMatch()))
@decorate(GroupPermission.require())
async def info_whitelist(app: Ariadne, group: Group, source: Source, message: MessageChain):
    if not is_init:
        await app.send_message(group, MessageChain(Plain('数据库初始化中，请稍后再试...')))
        return
    elif group.id not in module_config.activeGroups:
        return
    msg = message.split(' ')

    match len(msg):
        case 3:
            if msg[2].only(At):
                target = msg[2].get_first(At).target
                await t(app, group, source, target)
                return
        case 4:
            if msg[2].only(Plain):
                func = str(msg[2])
                if func == 'qq':
                    if msg[3].only(At):
                        target = msg[3].get_first(At).target
                        await t(app, group, source, target)
                    elif msg[3].only(Plain):
                        target = str(msg[3])
                        if target.isdigit():
                            await t(app, group, source, int(target))
                        else:
                            await app.send_message(group, MessageChain(Plain('无效的 QQ 号')), quote=source)
                        return
                elif func == 'id' and msg[3].only(Plain):
                    target = str(msg[3])
                    if await is_mc_id(target):
                        status, uuid_list = await query_whitelist_by_id(target)
                        if status['code'] == 200:
                            if uuid_list is None:
                                await app.send_message(group, MessageChain(Plain('没有使用该 ID 的白名单')), quote=source)
                            else:
                                player = await query_player_by_uuid(uuid_list.uuid)
                                if player is None:
                                    await app.send_message(group, MessageChain(Plain('没有使用该 ID 的 QQ')), quote=source)
                                else:
                                    await app.send_message(group, await gen_query_info_text(player), quote=source)
                        elif status['code'] == 204:
                            await app.send_message(group, MessageChain(Plain('没有使用该 ID 的正版用户')), quote=source)
                        elif status['code'] == 400:
                            await app.send_message(group, MessageChain(Plain('无效的正版用户名')), quote=source)
                        elif status['code'] == 500:
                            await app.send_message(group, MessageChain(Plain('Mojang API超时')), quote=source)
                        else:
                            await app.send_message(group, MessageChain(Plain('在查询使用该 ID 的正版用户时出错')), quote=source)
                    else:
                        await app.send_message(group, MessageChain(Plain('目标 ID 不是有效的 Minecraft 正版ID')), quote=source)
                    return
                elif func == 'uuid' and msg[3].only(Plain):
                    target = str(msg[3])
                    if _ := (await is_uuid(target)):
                        uuid_list = await query_whitelist_by_uuid(_)
                        if uuid_list is None:
                            await app.send_message(group, MessageChain('没有使用该 UUID 的白名单'), quote=source)
                        else:
                            player = await query_player_by_uuid(uuid_list.uuid)
                            if player is None:
                                await app.send_message(group, MessageChain(Plain('没有使用该 ID 的 QQ')), quote=source)
                            else:
                                await app.send_message(group, await gen_query_info_text(player), quote=source)
                    else:
                        await app.send_message(group, MessageChain(Plain('目标不是有效的 UUID')), quote=source)
                    return

    await app.send_message(group, MessageChain(Plain('参数错误，无效的命令')), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]wl clear')))
@decorate(GroupPermission.require(MemberPerm.Administrator))
async def clear_whitelist(app: Ariadne, group: Group, member: Member, source: Source, message: MessageChain):
    if not is_init:
        await app.send_message(group, MessageChain(Plain('数据库初始化中，请稍后再试...')))
        return
    elif group.id not in module_config.activeGroups:
        return
    msg = message.split(' ')
    if len(msg) != 2:
        await app.send_message(group, MessageChain(Plain('参数错误，无效的命令')), quote=source)
        return

    await app.send_message(
        group,
        MessageChain(
            At(member.id),
            Plain(
                ' 你正在清空本 bot 的服务器白名单数据库，本次操作不可逆，且不影响服务器的白名单，请问是否确认要清空本 bot 的服务器白名单数据库？'
                '\n确认请在10s内发送 .confirm ，取消请发送 .cancel'
            ),
        ),
        quote=source,
    )

    async def waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain, waiter_source: Source
    ) -> bool | None:
        if waiter_group.id == group.id and waiter_member.id == member.id:
            saying = str(waiter_message)
            if saying == '.confirm':
                return True
            elif saying == '.cancel':
                return False
            else:
                await app.send_message(
                    group, MessageChain(At(member.id), Plain('请发送 .confirm 或 .cancel')), quote=waiter_source
                )

    answer = await FunctionWaiter(waiter, [GroupMessage]).wait(timeout=10)
    if answer is None:
        await app.send_message(group, MessageChain(Plain('已超时取消')), quote=source)
        return
    if not answer:
        await app.send_message(group, MessageChain(Plain('已取消操作')), quote=source)
        return

    logger.warning(f'管理 {member.name}({member.id}) 正在清空白名单数据库')
    if await db.delete_many_exist(await db.select_all(select(Player))):
        await app.send_message(group, MessageChain(Plain('已清空白名单数据库，服务器白名单请自行处理')), quote=source)
    else:
        await app.send_message(group, MessageChain(Plain('清空白名单数据库失败')), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]myid').space(SpacePolicy.FORCE), WildcardMatch()))
@decorate(GroupPermission.require())
async def myid(app: Ariadne, group: Group, member: Member, source: Source, message: MessageChain):
    if not is_init:
        await app.send_message(group, MessageChain(Plain('数据库初始化中，请稍后再试...')))
        return
    elif group.id not in module_config.activeGroups:
        return
    msg = message.split(' ')
    if len(msg) != 2 or not msg[1].only(Plain):
        await app.send_message(group, MessageChain(Plain('参数错误，无效的命令')), quote=source)
        return

    mc_id = str(msg[1])
    if not await is_mc_id(mc_id):
        await app.send_message(group, MessageChain(Plain('目标 ID 不是有效的 Minecraft 正版ID')), quote=source)
        return
    target = member.id
    result = await add_whitelist_to_qq(target, mc_id, member.permission >= MemberPerm.Administrator)
    if result[1] and mc_id.lower() not in member.name.lower():
        try:
            await app.modify_member_info(member, MemberInfo(name=mc_id))
        except UnknownTarget as e:
            await app.send_message(group, MessageChain(Plain(f'请修改你的群名片为你申请白名单的ID\n（发生内部错误，请联系管理员：{e}）')), quote=source)
        else:
            await app.send_message(group, MessageChain(At(target), Plain(' 呐呐呐，白名单给你!\n已自动为你更改群名片')), quote=source)
        return
    await app.send_message(group, result[0], quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]list')))
@decorate(GroupPermission.require())
async def get_player_list(app: Ariadne, group: Group):
    if group.id not in module_config.activeGroups:
        return
    try:
        exec_result: str = await execute_command('list')  # noqa
    except TimeoutError:
        await app.send_message(group, MessageChain(Plain('连接服务器超时')))
        logger.error('rcon连接服务器超时')
        return
    except ValueError as e:
        await app.send_message(group, MessageChain(Plain(f'在服务器执行命令时出错：{e}')))
        logger.error('在服务器执行命令时出错')
        logger.exception(e)
        return

    player_list: list = exec_result.split(':')
    if player_list[1] == '':
        await app.send_message(group, MessageChain(Plain('服务器目前没有在线玩家')))
    else:
        playerlist = player_list[0].replace('There are', '服务器在线玩家数: ').replace(' of a max of ', '/')
        playerlist = playerlist.replace('players online', '\n在线列表: ')
        await app.send_message(group, MessageChain(Plain(playerlist + player_list[1].strip())))


# ---------------------------------------------------------------------------------------------------------------------


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]run'), WildcardMatch()))
@decorate(GroupPermission.require(MemberPerm.Administrator))
async def run_command_list(app: Ariadne, group: Group, message: MessageChain, source: Source):
    if group.id not in module_config.activeGroups:
        return
    split_msg = str(message).split(' ', 1)
    if len(split_msg) != 2:
        await app.send_message(group, MessageChain(Plain('参数错误，无效的命令')), quote=source)
        return
    try:
        exec_result: str = await execute_command(split_msg[1])
        logger.info(f'在服务器上执行命令：{split_msg[1]}')
    except TimeoutError:
        await app.send_message(group, MessageChain(Plain('连接服务器超时')))
        logger.error('rcon连接服务器超时')
        return
    except ValueError as e:
        await app.send_message(group, MessageChain(Plain(f'在服务器执行命令时出错：{e}')), quote=source)
        logger.error(f'在服务器执行命令 {split_msg[1]} 时出错')
        logger.exception(e)
        return

    if not exec_result:
        await app.send_message(group, MessageChain(Plain('服务器返回为空')), quote=source)
    else:
        await app.send_message(group, MessageChain(Plain(f'服务器返回 👇\n{exec_result}')), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@listen(MemberJoinEvent)
async def member_join(group: Group, member: Member):
    if not is_init or group.id != module_config.serverGroup:
        return
    result = await query_player_by_qq(member.id)
    if result is None:
        await db.add(Player(qq=member.id, joinTime=member.join_timestamp * 1000 if member.join_timestamp else None))
    else:
        result.joinTime = member.join_timestamp * 1000 if member.join_timestamp else None
        result.leaveTime = None
        await db.update_exist(result)


# ---------------------------------------------------------------------------------------------------------------------


@listen(MemberLeaveEventQuit)
async def member_leave(app: Ariadne, group: Group, member: Member):
    if not is_init or group.id != module_config.serverGroup:
        return
    result = await query_player_by_qq(member.id)
    if result is None:
        await db.add(
            Player(
                qq=member.id,
                joinTime=member.join_timestamp * 1000 if member.join_timestamp else None,
                leaveTime=int(time.time() * 1000),
            )
        )
    else:
        result.leaveTime = int(time.time() * 1000)
        await db.update_exist(result)
        await app.send_message(
            group, MessageChain(f'{member.name}({member.id})退群了') + await del_whitelist_by_qq(member.id)
        )


# ---------------------------------------------------------------------------------------------------------------------


@listen(MemberLeaveEventKick)
async def member_kick(app: Ariadne, group: Group, target: Member):
    if not is_init or group.id != module_config.serverGroup:
        return
    result = await query_player_by_qq(target.id)
    time_now = int(time.time() * 1000)
    if result is None:
        await db.add(
            Player(
                qq=target.id,
                joinTime=target.join_timestamp * 1000 if target.join_timestamp else None,
                leaveTime=time_now,
            )
        )
    else:
        result.leaveTime = time_now
        await db.update_exist(result)

    await db.add(
        BannedQQList(
            qq=target.id,
            banStartTime=time_now,
            banEndTime=int(datetime(2030, 1, 1, 0, 0, 0).timestamp()) * 1000,
            banReason='Kick',
            pardon=False,
            operater=10086,
        )
    )

    await app.send_message(
        group,
        MessageChain(f'{target.name}({target.id})被踢了') + await del_whitelist_by_qq(target.id),
    )


# ---------------------------------------------------------------------------------------------------------------------


# @listen(GroupMessage)
# @dispatch(Twilight(RegexMatch(r'[!！.]pardon').space(SpacePolicy.FORCE), WildcardMatch()))
# @decorate(GroupPermission.require(MemberPerm.Administrator))
# async def pardon(app: Ariadne, group: Group, message: MessageChain, source: Source):
#     if not is_init:
#         await app.send_message(group, MessageChain(Plain('数据库初始化中，请稍后再试...')))
#         return
#     elif group.id not in module_config.activeGroups:
#         return
#     msg = message.split(' ')
#     if len(msg) != 2:
#         await app.send_message(group, MessageChain(Plain('参数错误，无效的命令')), quote=source)
#         return
#     elif msg[1].only(At):
#         target = msg[1].get_first(At).target
#         await db.exec(update(BannedQQList).where(BannedQQList.qq == target).values(banned=False, ban=None))
#     elif msg[1].only(Plain):
#         target = str(msg[1])
#         if not target.isdigit():
#             await app.send_message(group, MessageChain(Plain('请输入QQ号')), quote=source)
#             return
#         await db.exec(update(PlayerInfo).where(PlayerInfo.qq == target).values(blocked=False, block_reason=None))
#         target = int(target)
#     else:
#         await app.send_message(group, MessageChain(Plain('参数错误，无效的命令')), quote=source)
#         return
#     player = await query_uuid_by_qq(target)
#     if player is None:
#         await app.send_message(group, MessageChain(Plain('已解封该玩家')), quote=source)
#         return
#     flags = []
#     if player.uuid1 is not None:
#         try:
#             mc_id = await get_mc_id(player.uuid1)
#         except asyncio.exceptions.TimeoutError as e:
#             await app.send_message(group, MessageChain(Plain(f'无法查询【{player.uuid1}】对应的正版id: 👇\n{e}')), quote=source)
#             logger.error(f'无法查询【{player.uuid1}】对应的正版id')
#             logger.exception(e)
#             flags.append(False)
#         else:
#             if isinstance(mc_id, str):
#                 try:
#                     res = await execute_command(f'pardon {mc_id}')
#                 except TimeoutError:
#                     await app.send_message(group, MessageChain(Plain('连接服务器超时')))
#                     logger.error('rcon连接服务器超时')
#                     flags.append(False)
#                 except ValueError as e:
#                     logger.exception(e)
#                     flags.append(False)
#                 else:
#                     if not res.startswith('Unbanned') and res != 'Nothing changed. The player isn\'t banned':
#                         await app.send_message(group, MessageChain(Plain(f'在解封该玩家时服务器返回未知结果 👇\n{res}')), quote=source)
#                         flags.append(False)
#             else:
#                 await app.send_message(
#                     group, MessageChain(Plain(f'无法获取该玩家的 ID，因此无法在服务器解封该玩家\nUUID：{player.uuid1}')), quote=source
#                 )
#                 flags.append(False)
#     if player.uuid2:
#         try:
#             mc_id = await get_mc_id(player.uuid2)
#         except asyncio.exceptions.TimeoutError as e:
#             await app.send_message(group, MessageChain(Plain(f'无法查询【{player.uuid2}】对应的正版id: 👇\n{e}')), quote=source)
#             logger.error(f'无法查询【{player.uuid2}】对应的正版id')
#             logger.exception(e)
#             flags.append(False)
#         else:
#             if isinstance(mc_id, str):
#                 try:
#                     res = await execute_command(f'pardon {mc_id}')
#                 except TimeoutError:
#                     await app.send_message(group, MessageChain(Plain('连接服务器超时')))
#                     logger.error('rcon连接服务器超时')
#                     flags.append(False)
#                 except ValueError as e:
#                     logger.exception(e)
#                     flags.append(False)
#                 else:
#                     if not res.startswith('Unbanned') and res != 'Nothing changed. The player isn\'t banned':
#                         await app.send_message(group, MessageChain(Plain(f'在解封该玩家时服务器返回未知结果 👇\n{res}')), quote=source)
#                         flags.append(False)
#             else:
#                 await app.send_message(
#                     group, MessageChain(Plain(f'无法获取该玩家的 ID，因此无法在服务器解封该玩家\nUUID：{player.uuid2}')), quote=source
#                 )
#                 flags.append(False)
#     if False not in flags:
#         await app.send_message(group, MessageChain(Plain('已解封该玩家')), quote=source)
#     else:
#         await app.send_message(group, MessageChain(Plain('在服务器解封该玩家时出现错误')), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]ban').space(SpacePolicy.FORCE), WildcardMatch()))
@decorate(GroupPermission.require(MemberPerm.Administrator))
async def ban(app: Ariadne, group: Group, message: MessageChain, source: Source):
    if not is_init:
        await app.send_message(group, MessageChain(Plain('数据库初始化中，请稍后再试...')))
        return
    elif group.id not in module_config.activeGroups:
        return
    msg = message.split(' ')
    if not 2 <= len(msg) <= 3:
        await app.send_message(group, MessageChain(Plain('参数错误，无效的命令')), quote=source)
        return
    elif msg[1].only(At):
        block_reason = str(msg[2].include(Plain).merge()) if len(msg) == 3 else 'None'
        target = msg[1].get_first(At).target
        await db.add(
            BannedQQList(
                qq=target,
                banStartTime=int(time.time() * 1000),
                banEndTime=int(datetime(2030, 1, 1, 0, 0, 0).timestamp()) * 1000,
                banReason=block_reason,
                pardon=False,
                operater=10086,
            )
        )
        await del_whitelist_by_qq(target)
    elif msg[1].only(Plain):
        block_reason = str(msg[2].include(Plain).merge()) if len(msg) == 3 else 'None'
        target = str(msg[1])
        if not target.isdigit():
            await app.send_message(group, MessageChain(Plain('请输入QQ号')))
            return
        await db.add(
            BannedQQList(
                qq=int(target),
                banStartTime=int(time.time() * 1000),
                banEndTime=int(datetime(2030, 1, 1, 0, 0, 0).timestamp()) * 1000,
                banReason=block_reason,
                pardon=False,
                operater=10086,
            )
        )
        await del_whitelist_by_qq(int(target))
    else:
        await app.send_message(group, MessageChain(Plain('参数错误，无效的命令')), quote=source)
        return
