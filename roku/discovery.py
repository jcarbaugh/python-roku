"""
Code adapted from Dan Krause.
https://gist.github.com/dankrause/6000248
http://github.com/dankrause
"""
import socket
import httplib
import StringIO

ST_DIAL = 'urn:dial-multiscreen-org:service:dial:1'
ST_ECP = 'roku:ecp'


class SSDPResponse(object):

    class _FakeSocket(StringIO.StringIO):
        def makefile(self, *args, **kw):
            return self

    def __init__(self, response):
        r = httplib.HTTPResponse(self._FakeSocket(response))
        r.begin()
        self.location = r.getheader('location')
        self.usn = r.getheader('usn')
        self.st = r.getheader('st')
        self.cache = r.getheader('cache-control').split('=')[1]

    def __repr__(self):
        return '<SSDPResponse({location}, {st}, {usn})'.format(**self.__dict__)


def discover(timeout=2, retries=1, st=ST_ECP):

    group = ('239.255.255.250', 1900)

    message = '\r\n'.join([
        'M-SEARCH * HTTP/1.1',
        'HOST: {0}:{1}'.format(*group),
        'MAN: "ssdp:discover"',
        'ST: {st}','MX: 3','',''])

    socket.setdefaulttimeout(timeout)

    responses = {}

    for _ in range(retries):

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(message.format(st=st), group)

        while 1:
            try:
                response = SSDPResponse(sock.recv(1024))
                responses[response.location] = response
            except socket.timeout:
                break

    return responses.values()
