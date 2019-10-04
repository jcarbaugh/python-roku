import os
from urllib.parse import quote_plus

import pytest

from roku.core import Application, Roku, COMMANDS
from roku.util import serialize_apps


TESTS_PATH = os.path.abspath(os.path.dirname(__file__))


class Fauxku(Roku):
    def __init__(self, *args, **kwargs):
        super(Fauxku, self).__init__(*args, **kwargs)
        self._calls = []

    def _call(self, method, path, *args, **kwargs):
        self._calls.append((method, path, args, kwargs))
        return ""

    def calls(self):
        return self._calls

    def last_call(self):
        return self._calls[-1]


@pytest.fixture
def roku():
    return Fauxku("0.0.0.0")


@pytest.fixture
def apps(roku):
    faux_apps = [
        Application("11", "1.0.1", "Fauxku Channel Store", roku),
        Application("22", "2.0.2", "Faux Netflix", roku),
        Application("33", "3.0.3", "Faux YouTube", roku),
        Application("44HL", "4.0.4", "Faux Hulu", roku),
    ]
    return faux_apps


def test_apps(mocker, roku):
    faux_apps = (Application("0x", "1.2.3", "Fauxku Channel Store"),)

    mocked_get = mocker.patch.object(Roku, "_get")
    mocked_get.return_value = serialize_apps(faux_apps)

    apps = roku.apps

    assert len(apps) == 1
    assert apps[0].id == "0x"
    assert apps[0].version == "1.2.3"
    assert apps[0].name == "Fauxku Channel Store"


def test_app_selector(mocker, apps):
    mocked_get = mocker.patch.object(Roku, "_get")
    mocked_get.return_value = serialize_apps(apps)

    for app in apps:
        roku = app.roku
        assert roku[app.id] == app
        assert roku[app.name] == app


def test_device_info(mocker, roku):
    xml_path = os.path.join(TESTS_PATH, "responses", "device-info.xml")
    with open(xml_path) as infile:
        content = infile.read()

    mocked_get = mocker.patch.object(Roku, "_get")
    mocked_get.return_value = content.encode("utf-8")

    d = roku.device_info

    assert d.model_name == "Roku 3"
    assert d.model_num == "4200X"
    assert d.software_version == "7.00.09044"
    assert d.serial_num == "111111111111"
    assert d.roku_type == "Stick"


def test_media_player(mocker, roku):
    xml_path = os.path.join(TESTS_PATH, "responses", "media-player.xml")
    with open(xml_path) as infile:
        content = infile.read()

    faux_apps = (Application(33, "1.2.3", "Faux YouTube"),)

    mocked_get = mocker.patch.object(Roku, "_get")
    mocked_get.return_value = content.encode("utf-8")
    mocker.patch.object(Roku, "apps", new=faux_apps)

    m = roku.media_player

    assert m.state == "pause"
    assert m.app.name == "Faux YouTube"
    assert m.position == 11187
    assert m.duration == 1858000


def test_commands(roku):
    for cmd in roku.commands:
        if cmd in ["literal", "search"]:
            # there is a separate test for the literal and search command
            continue

        getattr(roku, cmd)()
        call = roku.last_call()

        assert call == ("POST", f"/keypress/{COMMANDS[cmd]}", (), {})


def test_search(roku):
    text = "Stargate"
    roku.search(title=text)

    call = roku.last_call()

    assert call == ("POST", "/search/browse", (), {"params": {"title": text}})


def test_literal(roku):
    text = "Stargate"
    roku.literal(text)

    for i, call in enumerate(roku.calls()):
        assert call == ("POST", f"/keypress/Lit_{quote_plus(text[i])}", (), {})


def test_literal_fancy(roku):
    text = r"""~!@#$%^&*()_+`-=[]{};':",./<>?\|€£"""
    roku.literal(text)

    for i, call in enumerate(roku.calls()):
        assert call == ("POST", f"/keypress/Lit_{quote_plus(text[i])}", (), {})


def test_store(apps):
    for app in apps:
        roku = app.roku
        roku.store(app)
        call = roku.last_call()

        params = {"params": {"contentID": app.id}}
        assert call == ("POST", "/launch/11", (), params)


def test_launch(apps):
    for app in apps:
        roku = app.roku
        roku.launch(app)
        call = roku.last_call()

        params = {"params": {"contentID": app.id}}
        assert call == ("POST", f"/launch/{app.id}", (), params)


def test_icon_url(apps):
    for app in apps:
        assert app.roku.icon_url(app) == f"http://0.0.0.0:8060/query/icon/{app.id}"
        assert app.icon_url == f"http://0.0.0.0:8060/query/icon/{app.id}"
