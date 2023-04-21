"""
Code adapted from Dan Krause.
https://gist.github.com/dankrause/6000248
http://github.com/dankrause
"""
import socket
from http.client import HTTPResponse
from io import BytesIO

ST_DIAL = "urn:dial-multiscreen-org:service:dial:1"
ST_ECP = "roku:ecp"


class _FakeSocket(BytesIO):
    def makefile(self, *args, **kw):
        return self


class SSDPResponse(object):
    def __init__(self, response):
        self.location = response.getheader("location")
        self.usn = response.getheader("usn")
        self.st = response.getheader("st")
        self.cache = response.getheader("cache-control").split("=")[1]

    def __repr__(self):
        return f"<SSDPResponse({self.location}, {self.st}, {self.usn})"


def discover(timeout=2, retries=1, st=ST_ECP):
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

    socket.setdefaulttimeout(timeout)

    responses = {}

    for _ in range(retries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        m = message.format(st=st)
        sock.sendto(m.encode(), group)

        while 1:
            try:
                rhttp = HTTPResponse(_FakeSocket(sock.recv(1024)))
                rhttp.begin()
                if rhttp.status == 200:
                    rssdp = SSDPResponse(rhttp)
                    responses[rssdp.location] = rssdp
            except socket.timeout:
                break

    return responses.values()
