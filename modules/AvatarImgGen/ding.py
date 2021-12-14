#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO
from pathlib import Path

import httpx
from graia.ariadne.util.async_exec import cpu_bound
from PIL import Image as Img

pos_and_sizes = [
    [[183, 62], [95, 95]],
    [[185, 76], [93, 95]],
    [[184, 99], [97, 96]],
    [[185, 120], [99, 93]],
    [[157, 195], [148, 44]],
    [[179, 136], [119, 68]],
    [[176, 67], [119, 82]],
    [[176, 35], [116, 92]],
    [[181, 36], [106, 89]],
    [[182, 55], [99, 89]],
    [[184, 60], [95, 89]],
    [[183, 62], [95, 95]],
    [[185, 76], [93, 95]],
    [[184, 99], [97, 96]],
    [[179, 120], [109, 93]],
    [[157, 195], [148, 44]],
    [[179, 136], [119, 68]],
    [[176, 67], [119, 82]],
    [[171, 43], [127, 93]],
    [[176, 35], [116, 92]],
    [[181, 37], [106, 88]],
    [[182, 56], [98, 88]],
    [[184, 60], [95, 88]],
    [[183, 62], [95, 95]],
    [[185, 76], [93, 95]],
    [[184, 99], [96, 96]],
    [[179, 120], [109, 93]],
    [[157, 195], [148, 44]],
    [[179, 136], [119, 68]],
    [[177, 68], [118, 81]],
    [[172, 43], [125, 93]],
    [[176, 36], [116, 91]],
    [[181, 36], [106, 89]],
    [[182, 56], [99, 88]],
    [[184, 60], [95, 89]],
    [[184, 62], [93, 95]],
    [[185, 76], [93, 95]],
    [[185, 99], [95, 96]],
    [[179, 120], [109, 93]],
    [[157, 195], [149, 44]],
    [[179, 136], [119, 68]],
    [[177, 67], [118, 82]],
    [[172, 44], [125, 92]],
    [[176, 36], [116, 91]],
    [[181, 37], [106, 88]],
    [[182, 56], [98, 88]],
    [[184, 60], [95, 89]],
    [[183, 63], [95, 93]],
    [[185, 77], [93, 94]],
    [[184, 99], [96, 96]],
    [[180, 120], [107, 92]],
    [[158, 196], [147, 42]],
    [[180, 137], [117, 66]],
    [[178, 68], [116, 80]],
    [[172, 44], [125, 91]],
    [[176, 36], [115, 90]],
    [[181, 37], [105, 87]],
    [[183, 57], [96, 86]],
    [[185, 61], [92, 86]],
    [[184, 63], [93, 93]],
    [[187, 78], [89, 91]],
    [[185, 100], [94, 94]],
    [[180, 121], [107, 91]],
    [[158, 196], [147, 42]],
    [[180, 137], [117, 66]],
    [[177, 68], [117, 81]],
    [[172, 44], [125, 91]],
    [[177, 36], [114, 90]],
    [[182, 37], [104, 87]],
    [[183, 56], [97, 87]],
    [[185, 61], [92, 86]],
    [[184, 63], [93, 93]],
    [[187, 78], [89, 91]],
    [[185, 100], [94, 94]],
    [[180, 121], [107, 91]],
    [[158, 196], [147, 42]],
    [[180, 137], [117, 66]],
    [[177, 68], [117, 81]],
    [[172, 44], [125, 91]],
    [[177, 36], [114, 90]],
    [[182, 37], [104, 87]],
    [[183, 56], [97, 87]],
    [[185, 61], [92, 86]],
    [[185, 73], [86, 92]],
    [[183, 134], [86, 95]],
]

# QQ头像API：https://www.cnblogs.com/XiaoJun6/p/13053635.html
# QQ头像API：https://blog.soarli.top/archives/422.html


@cpu_bound
def ding(qq: int | str) -> bytes:
    resp = httpx.get(f'http://q.qlogo.cn/headimg_dl?dst_uin={qq}&spec=640&img_type=jpg')
    avatar = Img.open(BytesIO(resp.content))

    frames = []
    times = len(pos_and_sizes)
    for i in range(0, 121):  # 0-120
        if i < times:
            n_avatar = avatar.resize(pos_and_sizes[i][1], Img.LANCZOS)
            bg = Img.open(Path(Path(__file__).parent, 'res', 'ding', f'{i+1}.png'))
            canvas = Img.new('RGBA', bg.size, '#ffffff')
            canvas.paste(n_avatar, pos_and_sizes[i][0])
            canvas.paste(bg, mask=bg.split()[3])
            frames.append(canvas)
        else:
            bg = Img.open(Path(Path(__file__).parent, 'res', 'ding', f'{i+1}.png'))
            canvas = Img.new('RGBA', bg.size, '#ffffff')
            canvas.paste(bg)
            frames.append(canvas)

    img_io = BytesIO()
    frames[0].save(img_io, format='GIF', save_all=True, duration=1, append_Imgs=frames[1:], optimize=True, loop=False)
    return img_io.getvalue()
