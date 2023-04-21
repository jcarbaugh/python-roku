import logging
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus, urlparse
import socket
import requests

from . import discovery
from .util import deserialize_apps, deserialize_channels


__version__ = "4.1.0"


COMMANDS = {
    # Standard Keys
    "home": "Home",
    "reverse": "Rev",
    "forward": "Fwd",
    "play": "Play",
    "select": "Select",
    "left": "Left",
    "right": "Right",
    "down": "Down",
    "up": "Up",
    "back": "Back",
    "replay": "InstantReplay",
    "info": "Info",
    "backspace": "Backspace",
    "search": "Search",
    "enter": "Enter",
    "literal": "Lit",
    # For devices that support "Find Remote"
    "find_remote": "FindRemote",
    # For Roku TV
    "volume_down": "VolumeDown",
    "volume_up": "VolumeUp",
    "volume_mute": "VolumeMute",
    # For Roku TV while on TV tuner channel
    "channel_up": "ChannelUp",
    "channel_down": "ChannelDown",
    # For Roku TV current input
    "input_tuner": "InputTuner",
    "input_hdmi1": "InputHDMI1",
    "input_hdmi2": "InputHDMI2",
    "input_hdmi3": "InputHDMI3",
    "input_hdmi4": "InputHDMI4",
    "input_av1": "InputAV1",
    # For devices that support being turned on/off
    "power": "Power",
    "poweroff": "PowerOff",
    "poweron": "PowerOn",
}

SENSORS = ("acceleration", "magnetic", "orientation", "rotation")

TOUCH_OPS = ("up", "down", "press", "move", "cancel")


roku_logger = logging.getLogger("roku")


class RokuException(Exception):
    pass


class Application(object):
    def __init__(self, id, version, name, roku=None, is_screensaver=False):
        self.id = str(id)
        self.version = version
        self.name = name
        self.is_screensaver = is_screensaver
        self.roku = roku

    def __eq__(self, other):
        return isinstance(other, Application) and (self.id, self.version) == (
            other.id,
            other.version,
        )

    def __repr__(self):
        return f"<Application: [{self.id}] {self.name} v{self.version}>"

    @property
    def icon(self):
        if self.roku:
            return self.roku.icon(self)

    @property
    def icon_url(self):
        if self.roku:
            return self.roku.icon_url(self)

    def launch(self):
        if self.roku:
            self.roku.launch(self)

    def store(self):
        if self.roku:
            self.roku.store(self)


class Channel(object):
    def __init__(self, number, name, roku=None):
        self.number = str(number)
        self.name = name
        self.roku = roku

    def __eq__(self, other):
        return isinstance(other, Channel) and (self.number, self.name) == (
            other.number,
            other.name,
        )

    def __repr__(self):
        return f"<Channel: [{self.number}] {self.name}>"

    def launch(self):
        if self.roku:
            tv_app = Application(
                id="tvinput.dtv", version=None, name="TV", roku=self.roku
            )
            self.roku.launch(tv_app, {"ch": self.number})


class DeviceInfo(object):
    def __init__(
        self,
        model_name,
        model_num,
        software_version,
        serial_num,
        user_device_name,
        roku_type,
    ):
        self.model_name = model_name
        self.model_num = model_num
        self.software_version = software_version
        self.serial_num = serial_num
        self.user_device_name = user_device_name
        self.roku_type = roku_type

    def __repr__(self):
        return (
            f"<DeviceInfo: {self.model_name}-{self.model_num}, "
            f"SW v{self.software_version}, "
            f"Ser# {self.serial_num} ({self.roku_type})>"
        )


class MediaPlayer(object):
    def __init__(self, state, app, position, duration):
        self.state = state
        self.app = app
        self.position = position
        self.duration = duration

    def __repr__(self):
        return "<MediaPlayer: %s in %s at %s/%s ms>" % (
            self.state,
            self.app.name,
            self.position,
            self.duration,
        )


class Roku(object):
    @classmethod
    def discover(self, *args, **kwargs):
        rokus = []
        for device in discovery.discover(*args, **kwargs):
            o = urlparse(device.location)
            rokus.append(Roku(o.hostname, o.port))
        return rokus

    def __init__(self, host, port=8060, timeout=10):
        self.host = socket.gethostbyname(host)
        self.port = port
        self._conn = None
        self.timeout = timeout

    def __repr__(self):
        return f"<Roku: {self.host}:{self.port}>"

    def __getattr__(self, name):
        if name not in COMMANDS and name not in SENSORS:
            raise AttributeError(f"{name} is not a valid method")

        def command(*args, **kwargs):
            if name in SENSORS:
                keys = [f"{name}.{axis}" for axis in ("x", "y", "z")]
                params = dict(zip(keys, args))
                self.input(params)
            elif name == "literal":
                for char in args[0]:
                    path = f"/keypress/{COMMANDS[name]}_{quote_plus(char)}"
                    self._post(path)
            elif name == "search":
                path = "/search/browse"
                params = {k.replace("_", "-"): v for k, v in kwargs.items()}
                self._post(path, params=params)
            else:
                if len(args) > 0 and (args[0] == "keydown" or args[0] == "keyup"):
                    path = f"/{args[0]}/{COMMANDS[name]}"
                else:
                    path = f"/keypress/{COMMANDS[name]}"
                self._post(path)

        return command

    def __getitem__(self, key):
        key = str(key)
        app = self._app_for_name(key)
        if not app:
            app = self._app_for_id(key)
        return app

    def __dir__(self):
        return sorted(
            dir(type(self))
            + list(self.__dict__.keys())
            + list(COMMANDS.keys())
            + list(SENSORS)
        )

    def _app_for_name(self, name):
        for app in self.apps:
            if app.name == name:
                return app

    def _app_for_id(self, app_id):
        for app in self.apps:
            if app.id == app_id:
                return app

    def _connect(self):
        if self._conn is None:
            self._conn = requests.Session()

    def _get(self, path, *args, **kwargs):
        return self._call("GET", path, *args, **kwargs)

    def _post(self, path, *args, **kwargs):
        return self._call("POST", path, *args, **kwargs)

    def _call(self, method, path, *args, **kwargs):
        self._connect()

        roku_logger.debug(path)

        url = f"http://{self.host}:{self.port}{path}"

        if method not in ("GET", "POST"):
            raise ValueError("only GET and POST HTTP methods are supported")

        func = getattr(self._conn, method.lower())
        resp = func(url, timeout=self.timeout, *args, **kwargs)

        if resp.status_code < 200 or resp.status_code > 299:
            raise RokuException(resp.content)

        return resp.content

    @property
    def apps(self):
        resp = self._get("/query/apps")
        applications = deserialize_apps(resp)
        for a in applications:
            a.roku = self
        return applications

    @property
    def active_app(self):
        resp = self._get("/query/active-app")
        active_app = deserialize_apps(resp)
        if len(active_app):
            return active_app[0]
        else:
            return None

    @property
    def tv_channels(self):
        resp = self._get("/query/tv-channels")
        channels = deserialize_channels(resp)
        for c in channels:
            c.roku = self
        return channels

    @property
    def device_info(self):
        resp = self._get("/query/device-info")
        root = ET.fromstring(resp)

        roku_type = "Box"
        if root.find("is-tv") is not None and root.find("is-tv").text == "true":
            roku_type = "TV"
        elif root.find("is-stick") is not None and root.find("is-stick").text == "true":
            roku_type = "Stick"
        dinfo = DeviceInfo(
            model_name=root.find("model-name").text,
            model_num=root.find("model-number").text,
            software_version=f"{root.find('software-version').text}.{root.find('software-build').text}",
            serial_num=root.find("serial-number").text,
            user_device_name=root.find("user-device-name").text,
            roku_type=roku_type,
        )
        return dinfo

    @property
    def media_player(self):
        resp = self._get("/query/media-player")
        root = ET.fromstring(resp)

        mp = MediaPlayer(
            state=root.get("state"),
            app=self[int(root.find("plugin").get("id"))],
            position=int(root.find("position").text.split(" ", 1)[0]),
            duration=int(root.find("duration").text.split(" ", 1)[0]),
        )
        return mp

    @property
    def commands(self):
        return sorted(COMMANDS.keys())

    @property
    def power_state(self):
        resp = self._get("/query/device-info")
        root = ET.fromstring(resp)
        if root.find("power-mode").text:
            if root.find("power-mode").text == "PowerOn":
                return "On"
            else:
                return "Off"
        return "Unknown"

    def icon(self, app):
        return self._get(f"/query/icon/{app.id}")

    def icon_url(self, app):
        return "http://%s:%s/query/icon/%s" % (self.host, self.port, app.id)

    def launch(self, app, params={}):
        if app.roku and app.roku != self:
            raise RokuException("this app belongs to another Roku")
        params["contentID"] = app.id
        return self._post(f"/launch/{app.id}", params=params)

    def store(self, app):
        return self._post("/launch/11", params={"contentID": app.id})

    def input(self, params):
        return self._post("/input", params=params)

    def touch(self, x, y, op="down"):
        if op not in TOUCH_OPS:
            raise RokuException(f"{op} is not a valid touch operation")

        params = {
            "touch.0.x": x,
            "touch.0.y": y,
            "touch.0.op": op,
        }

        self.input(params)

    @property
    def current_app(self):
        resp = self._get("/query/active-app")
        root = ET.fromstring(resp)
        is_screensaver = True

        app_node = root.find("screensaver")
        if app_node is None:
            app_node = root.find("app")
            is_screensaver = False

        if app_node is None:
            return None

        return Application(
            id=app_node.get("id"),
            version=app_node.get("version"),
            name=app_node.text,
            is_screensaver=is_screensaver,
            roku=self,
        )
