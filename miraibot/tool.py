import aiohttp

from graia.application.message.elements.internal import Image

class mirai_codes:
    ctx: str = ''
    __logger: object

    def __init__(self, message, logger):
        self.__logger = logger
        for i in message.__root__:
            if hasattr(self, i.__class__.__name__):
                self.ctx += getattr(self, i.__class__.__name__)(i)
            else:
                self.__logger.error(f'mirai码解码失败, 解码失败的编码是:  {i}')

    def Source(self, type):
        return ''

    def Plain(self, data):
        return data.text

    def At(self, data):
        if data.display[0] == '@':
            data.display = data.display[1:]
        return f'[mirai=At, qq={data.target}, name={data.display}]'

    def Image(self, data):
        return f'[mirai=Image, id={data.imageId[1:-7]}, url={data.url}]'

    def Quote(self, data):
        _message = ''
        for i in data.origin.__root__:
            if hasattr(self, i.__class__.__name__):
                _message += getattr(self, i.__class__.__name__)(i)
        return f'[[mirai=Quote, id={data.id}, target={data.targetId}, sender={data.senderId}, text={_message}]]'

    def Face(self, data):
        _Facename = {'174': 'wunai', '175': 'maimeng',
                     '176': 'xiaojiujie',
                     '178': 'xieyanxiao', '179': 'doge',
                     '182': 'xiaoku', '177': 'penxie',
                     '212': 'tuosai'
                     }

        if data.name == '未知表情':
            if str(data.faceId) in _Facename:
                data.name = _Facename[f'{data.faceId}']
            else:
                self.__logger.error(data)

        return f'[mirai=Face, face={data.faceId}, name={data.name}]'

    def App(self,data):
        print(type(data))

def shell(message, logger):
    data = message.split(' ')
    if '' in data:
        data.remove('')
    return data

class http:
    @staticmethod
    async def post(url, **k):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, **k) as response:
                response.raise_for_status()
                return await response.read()

    @staticmethod
    async def get(url, **k):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, **k) as response:
                response.raise_for_status()
                return await response.read()

    @staticmethod
    async def upload(url, filedata: bytes, addon_dict: dict):
        upload_data = aiohttp.FormData()
        upload_data.add_field("img", filedata)
        for item in addon_dict.items():
            upload_data.add_fields(item)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=upload_data) as response:
                response.raise_for_status()
                return await response.text("utf-8")
