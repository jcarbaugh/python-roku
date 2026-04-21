import logging
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus, urlparse
import socket

import aiohttp

from ..constants import COMMANDS, SENSORS, TOUCH_OPS
from ..models import Application, DeviceInfo, MediaPlayer, RokuException
from ..util import deserialize_apps, deserialize_channels
from .discovery import discover as async_discover

roku_logger = logging.getLogger("roku")


class AsyncRoku(object):
    def __init__(self, host, port=8060, timeout=10):
        self.host = socket.gethostbyname(host)
        self.port = port
        self._session = None
        self.timeout = timeout

    @classmethod
    async def discover(cls, *args, **kwargs):
        rokus = []
        for device in await async_discover(*args, **kwargs):
            o = urlparse(device.location)
            rokus.append(cls(o.hostname, o.port))
        return rokus

    def __repr__(self):
        return f"<AsyncRoku: {self.host}:{self.port}>"

    def __getattr__(self, name):
        if name not in COMMANDS and name not in SENSORS:
            raise AttributeError(f"{name} is not a valid method")

        async def command(*args, **kwargs):
            if name in SENSORS:
                keys = [f"{name}.{axis}" for axis in ("x", "y", "z")]
                params = dict(zip(keys, args))
                await self.input(params)
            elif name == "literal":
                for char in args[0]:
                    path = f"/keypress/{COMMANDS[name]}_{quote_plus(char)}"
                    await self._post(path)
            elif name == "search":
                path = "/search/browse"
                params = {k.replace("_", "-"): v for k, v in kwargs.items()}
                await self._post(path, params=params)
            else:
                if len(args) > 0 and (args[0] == "keydown" or args[0] == "keyup"):
                    path = f"/{args[0]}/{COMMANDS[name]}"
                else:
                    path = f"/keypress/{COMMANDS[name]}"
                await self._post(path)

        return command

    def __dir__(self):
        return sorted(
            dir(type(self))
            + list(self.__dict__.keys())
            + list(COMMANDS.keys())
            + list(SENSORS)
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    def _connect(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def _get(self, path, **kwargs):
        return await self._call("GET", path, **kwargs)

    async def _post(self, path, **kwargs):
        return await self._call("POST", path, **kwargs)

    async def _call(self, method, path, **kwargs):
        self._connect()

        roku_logger.debug(path)

        url = f"http://{self.host}:{self.port}{path}"

        if method not in ("GET", "POST"):
            raise ValueError("only GET and POST HTTP methods are supported")

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with self._session.request(
            method, url, timeout=timeout, **kwargs
        ) as resp:
            if resp.status < 200 or resp.status > 299:
                raise RokuException(await resp.read())
            return await resp.read()

    async def get_apps(self):
        resp = await self._get("/query/apps")
        applications = deserialize_apps(resp)
        for a in applications:
            a.roku = self
        return applications

    async def get_active_app(self):
        resp = await self._get("/query/active-app")
        active_app = deserialize_apps(resp)
        if len(active_app):
            return active_app[0]
        else:
            return None

    async def get_tv_channels(self):
        resp = await self._get("/query/tv-channels")
        channels = deserialize_channels(resp)
        for c in channels:
            c.roku = self
        return channels

    async def get_device_info(self):
        resp = await self._get("/query/device-info")
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

    async def get_media_player(self):
        resp = await self._get("/query/media-player")
        root = ET.fromstring(resp)

        plugin = root.find("plugin")
        app = Application(
            id=plugin.get("id"),
            version=plugin.get("version"),
            name=plugin.text or "",
            roku=self,
        )

        # Duration isn't provided by all apps in all cases, e.g. Netflix / NOW TV
        duration_element = root.find("duration")
        duration = int(duration_element.text.split(" ", 1)[0]) if duration_element is not None else None

        mp = MediaPlayer(
            state=root.get("state"),
            app=app,
            position=int(root.find("position").text.split(" ", 1)[0]),
            duration=duration,
        )
        return mp

    @property
    def commands(self):
        return sorted(COMMANDS.keys())

    async def get_power_state(self):
        resp = await self._get("/query/device-info")
        root = ET.fromstring(resp)
        if root.find("power-mode").text:
            if root.find("power-mode").text == "PowerOn":
                return "On"
            else:
                return "Off"
        return "Unknown"

    async def icon(self, app):
        return await self._get(f"/query/icon/{app.id}")

    def icon_url(self, app):
        return "http://%s:%s/query/icon/%s" % (self.host, self.port, app.id)

    async def launch(self, app, params={}):
        if app.roku and app.roku != self:
            raise RokuException("this app belongs to another Roku")
        params["contentID"] = app.id
        return await self._post(f"/launch/{app.id}", params=params)

    async def store(self, app):
        return await self._post("/launch/11", params={"contentID": app.id})

    async def input(self, params):
        return await self._post("/input", params=params)

    async def touch(self, x, y, op="down"):
        if op not in TOUCH_OPS:
            raise RokuException(f"{op} is not a valid touch operation")

        params = {
            "touch.0.x": x,
            "touch.0.y": y,
            "touch.0.op": op,
        }

        await self.input(params)

    async def get_current_app(self):
        resp = await self._get("/query/active-app")
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
