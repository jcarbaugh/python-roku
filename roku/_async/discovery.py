"""
Async SSDP discovery for Roku devices.
"""

import asyncio
import socket
from http.client import HTTPResponse

from ..discovery import ST_ECP, SSDPResponse, _FakeSocket


class _SSDPProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.responses = {}
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            rhttp = HTTPResponse(_FakeSocket(data))
            rhttp.begin()
            if rhttp.status == 200:
                rssdp = SSDPResponse(rhttp)
                self.responses[rssdp.location] = rssdp
        except Exception:
            pass


async def discover(timeout=2, retries=1, st=ST_ECP):
    group = ("239.255.255.250", 1900)

    message = "\r\n".join(
        [
            "M-SEARCH * HTTP/1.1",
            f"HOST: {group[0]}:{group[1]}",
            'MAN: "ssdp:discover"',
            "ST: {st}",
            "MX: 3",
            "",
            "",
        ]
    )

    responses = {}
    loop = asyncio.get_running_loop()

    for _ in range(retries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.setblocking(False)

        transport, protocol = await loop.create_datagram_endpoint(
            _SSDPProtocol,
            sock=sock,
        )

        try:
            m = message.format(st=st)
            transport.sendto(m.encode(), group)
            await asyncio.sleep(timeout)
            responses.update(protocol.responses)
        finally:
            transport.close()

    return responses.values()
