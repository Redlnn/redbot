from io import BytesIO
from re import RegexFlag

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    ArgResult,
    ArgumentMatch,
    RegexMatch,
    RegexResult,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group
from graia.ariadne.util.async_exec import io_bound
from graia.saya import Channel
from graiax.shortcut.saya import decorate, dispatch, listen
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFilter, ImageFont
from PIL.ImageFont import FreeTypeFont

from libs.control import require_disable
from libs.control.permission import GroupPermission
from static.path import lib_path

channel = Channel.current()

channel.meta['name'] = '流浪地球2倒计时生成'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = (
    '小破球2倒计时生成\n\n用法：\n'
    '[.!！]倒计时 距月球危机\n'
    '还剩 16 秒\n'
    'THE LUNAR CRISIS\n'
    'IN 16 SECONDS\n\n参数：\n'
    '  --dark, -d, -D  黑暗模式\n'
    '  --gif, -g, -G  GIF图（1fps）\n'
)


@listen(GroupMessage)
@dispatch(
    Twilight(
        RegexMatch('[.!！]倒计时'),
        'target' @ WildcardMatch().flags(RegexFlag.DOTALL),
        'gif' @ ArgumentMatch('--gif', '-g', '-G', action="store_true"),
        'dark' @ ArgumentMatch('--dark', '-d', '-D', action="store_true"),
    )
)
@decorate(
    GroupPermission.require(),
    require_disable(channel.module),
    require_disable('core_modules.msg_loger'),
)
async def main(
    app: Ariadne,
    group: Group,
    target: RegexResult,
    gif: ArgResult[bool],
    dark: ArgResult[bool],
):
    if target.result is None:
        raise ValueError('输入格式不正确')

    try:
        cn_1, text2, en_1, en_2 = str(target.result).split('\n')
        prefix, number, suffix = text2.split(' ')
    except ValueError:
        await app.send_message(
            group, MessageChain('格式错误，注意空格和换行，参考：\n.倒计时 距月球危机\n还剩 16 秒\nTHE LUNAR CRISIS\nIN 16 SECONDS')
        )
        return

    cn_font = ImageFont.truetype(str(lib_path / 'fonts' / 'HarmonyOS_Sans_SC_Bold.ttf'), 100)
    number_font = ImageFont.truetype(str(lib_path / 'fonts' / 'HarmonyOS_Sans_SC_Bold.ttf'), 285)
    en_font = ImageFont.truetype(str(lib_path / 'fonts' / 'HarmonyOS_Sans_SC_Bold.ttf'), 45)
    font_color = '#eee' if dark.result else '#2c2c2c'
    bg_color = '#2c2c2c' if dark.result else '#eeeeee'

    if gif.result:
        frames: list[PILImage.Image] = []
        origin_num_len = len(number)
        for _ in range(int(number), 0, -1):
            current_num = str(_)
            current_num_len = len(current_num)
            num = (
                # 下面写死了2个空格，等宽字体应用1个空格
                " " * 2 * (origin_num_len - current_num_len) + current_num
                if current_num_len < origin_num_len
                else current_num
            )
            frames.append(
                await the_wondering_earth_counting_down(
                    cn_1, prefix, num, suffix, en_1, en_2, cn_font, number_font, en_font, font_color, bg_color
                )
            )
        with BytesIO() as f:
            frames[0].save(
                f,
                format='GIF',
                save_all=True,
                append_images=frames[1:],
                duration=1000,
                optimize=True,
                loop=0,
            )
            await app.send_message(group, MessageChain(Image(data_bytes=f.getvalue())))
    else:
        with BytesIO() as f:
            im = (
                await the_wondering_earth_counting_down(
                    cn_1, prefix, number, suffix, en_1, en_2, cn_font, number_font, en_font, font_color, bg_color
                )
            ).convert('RGB')
            im.save(f, format='JPEG', quality=90, optimize=True, progressive=True, subsampling=2, qtables='web_high')
            await app.send_message(group, MessageChain(Image(data_bytes=f.getvalue())))


def get_box(text: str, font: FreeTypeFont):
    bbox = font.getbbox(text)
    return bbox[0], -bbox[1], bbox[2], bbox[3] - bbox[1]  # startX, startY, width, height


@io_bound
def the_wondering_earth_counting_down(
    cn_1: str,
    prefix: str,
    number: str,
    suffix: str,
    en_1: str,
    en_2: str,
    cn_font: FreeTypeFont,
    number_font: FreeTypeFont,
    en_font: FreeTypeFont,
    font_color: str,
    bg_color: str,
) -> PILImage.Image:
    """流浪地球倒计时生成

    Args:
        text (str): 倒计时文本，格式：'距月球危机\n还剩 16 秒\nTHE LUNAR CRISIS\nIN 16 SECONDS'

    Returns:
        PILImage.Image: 图片生成结果的PILImage
    """

    en_1 = en_1.upper()
    en_2 = en_2.upper()

    box1 = get_box(cn_1, cn_font)
    box_prefix = get_box(prefix, cn_font)
    box_number = get_box(number, number_font)
    box_suffix = get_box(suffix, cn_font)
    box3 = get_box(en_1, en_font)
    box4 = get_box(en_2, en_font)

    MARGIN_TOP = 150
    MARGIN_LEFT = 125
    CN_ROW_SPACE = 30
    EN_ROW_SPACE = 20

    width = (
        2 * MARGIN_LEFT
        + box1[0]
        + box1[2]
        + max(box3[2] - box_prefix[2], box4[2] - box_prefix[2], box_number[2] + box_suffix[2])
    )
    height = (
        2 * MARGIN_TOP
        + box1[1]
        + box1[3]
        + box_prefix[3]
        - 2 * box_prefix[1]
        + box3[3]
        + box4[3]
        + 2 * CN_ROW_SPACE
        + EN_ROW_SPACE
    )

    im = PILImage.new('RGBA', (width, height), f'{bg_color}00')
    draw = ImageDraw.Draw(im, 'RGBA')

    draw.text((MARGIN_LEFT + box1[0], MARGIN_TOP + box1[1]), cn_1, font_color, cn_font)
    draw.text(
        (MARGIN_LEFT + box1[2] - box_prefix[0] - box_prefix[2], MARGIN_TOP + box1[1] + box1[3] + CN_ROW_SPACE),
        prefix,
        font_color,
        cn_font,
    )
    draw.text(
        (MARGIN_LEFT + box1[2] - box_prefix[0], MARGIN_TOP + box1[1] + box1[3] + box_prefix[3] + CN_ROW_SPACE),
        number,
        '#d03440',
        number_font,
        anchor='lb',
    )
    draw.text(
        (MARGIN_LEFT + box1[2] - box_prefix[0] + box_number[2], MARGIN_TOP + box1[1] + box1[3] + CN_ROW_SPACE),
        suffix,
        font_color,
        cn_font,
    )
    draw.text(
        (
            MARGIN_LEFT + box1[2] - box_prefix[0] - box_prefix[2],
            MARGIN_TOP + box1[1] + box1[3] + box_prefix[3] + 2 * CN_ROW_SPACE,
        ),
        en_1,
        font_color,
        en_font,
    )
    draw.text(
        (
            MARGIN_LEFT + box1[2] - box_prefix[0] - box_prefix[2],
            MARGIN_TOP + box1[1] + box1[3] + box_prefix[3] + box3[3] + 2 * CN_ROW_SPACE + EN_ROW_SPACE,
        ),
        en_2,
        font_color,
        en_font,
    )
    draw.rectangle(
        (
            MARGIN_LEFT + box1[2] - box_prefix[0] - box_prefix[2] - 25,
            MARGIN_TOP + box1[1] + box1[3] + CN_ROW_SPACE,
            MARGIN_LEFT + box1[2] - box_prefix[0] - box_prefix[2] - 15,
            MARGIN_TOP
            + box1[1]
            + box1[3]
            + box_prefix[3]
            - 2 * box_prefix[1]
            + box3[3]
            + box4[3]
            + 2 * CN_ROW_SPACE
            + EN_ROW_SPACE,
        ),
        '#d03440',
    )

    im_new = PILImage.new('RGBA', (width, height), f'{bg_color}ff')
    im_new.paste(im, (0, 0), mask=im.split()[3])
    im_new = im_new.filter(ImageFilter.GaussianBlur(5))

    # x, y = im_new.size
    # for i, k in itertools.product(range(x), range(y)):
    #     color = im_new.getpixel((i, k))
    #     color = color[:-1] + (int(0.4 * color[-1]),)
    #     im_new.putpixel((i, k), color)
    im_new = PILImage.blend(im_new, PILImage.new('RGBA', (width, height), f'{bg_color}00'), 0.33)

    im_result = PILImage.new('RGBA', (width, height), f'{bg_color}ff')
    im_result = PILImage.alpha_composite(im_result, im_new)
    im_result = PILImage.alpha_composite(im_result, im)

    # im_result.show()
    return im_result
