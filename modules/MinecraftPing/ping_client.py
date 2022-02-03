#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import struct
import time

import orjson as json
import regex as re
from graia.ariadne.util.async_exec import io_bound

from .aiodns_resolver import dns_resolver_srv

__all__ = ['ping']


class PingClient:
    """
    改自 https://github.com/djkcyl/ABot-Graia/blob/MAH-V2/saya/MinecraftPing/

    可能会报如下错误：
    1. ConnectionRefusedError: [WinError 10061] 由于目标计算机积极拒绝，无法连接。
    2. socket.timeout: timed out
    3. socket.gaierror 无效的主机名
    """

    def __init__(self, host='localhost', port=25565, timeout=5):
        self._host = host
        self._port = port
        self._timeout = timeout

    def _unpack_varint(self, sock):
        data = 0
        for i in range(5):
            ordinal = sock.recv(1)
            if len(ordinal) == 0:
                break

            byte = ord(ordinal)
            data |= (byte & 0x7F) << 7 * i

            if not byte & 0x80:
                break

        return data

    def _pack_varint(self, data):
        ordinal = b''

        while True:
            byte = data & 0x7F
            data >>= 7
            ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

            if data == 0:
                break

        return ordinal

    def _pack_data(self, data):
        if isinstance(data, str):
            data = data.encode('utf8')
            return self._pack_varint(len(data)) + data
        elif isinstance(data, int):
            return struct.pack('H', data)
        elif isinstance(data, float):
            return struct.pack('Q', int(data))
        else:
            return data

    def _send_data(self, sock, *args):
        data = b''

        for arg in args:
            data += self._pack_data(arg)

        sock.send(self._pack_varint(len(data)) + data)

    def _read_fully(self, sock, extra_varint=False) -> bytes:
        packet_length = self._unpack_varint(sock)
        packet_id = self._unpack_varint(sock)
        byte = b''

        if extra_varint:
            if packet_id > packet_length:
                self._unpack_varint(sock)

            extra_length = self._unpack_varint(sock)

            while len(byte) < extra_length:
                byte += sock.recv(extra_length)

        else:
            byte = sock.recv(packet_length)

        return byte

    def _format_desc(self, data: dict) -> str:
        if 'extra' in data:
            tmp = ''
            for part in data['extra']:
                tmp += part['text']
            return tmp
        elif 'text' in data:
            return re.sub(r'§[0-9a-gk-r]', '', data['text'])

    @io_bound
    def get_ping(self, format: bool = True) -> dict:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect((self._host, self._port))
            self._send_data(sock, b'\x00\x00', self._host, self._port, b'\x01')
            self._send_data(sock, b'\x00')
            data = self._read_fully(sock, extra_varint=True)

            self._send_data(sock, b'\x01', time.time() * 1000)
            unix = self._read_fully(sock)

        status = json.loads(data.decode('utf8'))
        if format:
            status['description'] = self._format_desc(status['description'])
        status['delay'] = time.time() * 1000 - struct.unpack('Q', unix)[0]
        return status


async def ping(ip: str | None = None, url: str | None = None, port: int | None = None) -> dict:
    if not ip and not url:
        raise ValueError('Neither IP nor URL exists')
    elif ip and url:
        raise ValueError('Both IP and URL exist')

    if ip:
        host = ip
    elif url and port:
        host = url
    else:  # url and not port
        host, port = await dns_resolver_srv(url)
        if not host:
            host = url
        port = port if port else 25565

    client = PingClient(host=host, port=port)
    stats: dict = await client.get_ping()

    if stats['players'].get('sample'):
        player_list: list = stats['players'].get('sample')
    else:
        player_list = []

    return {
        'version': stats['version']['name'],
        'protocol': str(stats['version']['protocol']),
        'motd': stats['description'],
        'delay': str(round(stats['delay'], 1)),
        'online_player': str(stats['players']['online']),
        'max_player': str(stats['players']['max']),
        'player_list': player_list,
    }
