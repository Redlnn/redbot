import aiohttp

def shell(message):
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
