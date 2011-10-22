#!/Users/Jeremy/.virtualenvs/sandbox/bin/python
from lxml import etree
import httplib
import logging
import socket

__version__ = '0.1.0'

roku_logger = logging.getLogger('roku')

COMMANDS = {
    'home': 'Home',
    'reverse': 'Rev',
    'forward': 'Fwd',
    'play': 'Play',
    'select': 'Select',
    'left': 'Left',
    'right': 'Right',
    'down': 'Down',
    'up': 'Up',
    'back': 'Back',
    'replay': 'InstantReplay',
    'info': 'Info',
    'backspace': 'Backspace',
    'search': 'Search',
    'enter': 'Enter',
    'literal': 'Lit',
}

class RokuException(Exception):
    pass

class Application(object):

    def __init__(self, id, version, name):
        self.id = id
        self.version = version
        self.name = name

    def __str__(self):
        return "[%s] %s v%s" % (self.id, self.name, self.version)

class Roku(object):

    def __init__(self, host, port=8060):
        self.host = host
        self.port = port
        self.conn = None
        self._connect()

    def __getattr__(self, name):

        if name not in COMMANDS:
            raise AttributeError('%s is not a valid method' % name)

        def command(*args):
            if name == 'literal':
                for char in args[0]:
                    path = '/keypress/%s_%s' % (COMMANDS[name], char.upper())
                    self._send(path)
            else:
                path = '/keypress/%s' % COMMANDS[name]
                self._send(path)

        return command

    def _connect(self):
        if self.conn is not None and hasattr(self.conn, 'close'):
            self.conn.close()
            self.conn = None
        self.conn = httplib.HTTPConnection('%s:%s' % (self.host, self.port))

    def _send(self, path):

        roku_logger.debug(path)

        try:

            self.conn.request('POST', path)
            resp = self.conn.getresponse()
            content = resp.read()

            if resp.status != 200:
                raise RokuException(content)

        except socket.error, se:
            raise RokuException(se.strerror)

        return content

    def apps(self):
        applications = []
        resp = self._send('/query/apps')
        root = etree.fromstring(resp)
        for app_node in root:
            app = Application(
                id=app_node.attrib['id'],
                version=app_node.attrib['version'],
                name=app_node.text,
            )
            applications.append(app)
        return applications

    def commands(self):
        return sorted(COMMANDS.keys())

    def get_app(self, name):
        for app in self.apps():
            if app.name == name:
                return app

    def get_icon(self, app):
        return self._send('/query/icon/%s' % app.id)

    def launch(self, app):
        return self._send('/launch/11?contentID=%s' % app.id)

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    r = Roku('localhost')

    print r.commands()

    r.home()
    r.literal('aweglksjgl')
    r.up()

    apps = r.apps()
    for app in apps:
        print "\t%s" % app

    app = r.get_app('Hulu Plus')
    print app

    r.get_icon(app)
    r.launch(app)
