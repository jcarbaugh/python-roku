import os
from unittest.mock import AsyncMock, patch
from urllib.parse import quote_plus

import pytest

from roku._async import AsyncRoku
from roku.constants import COMMANDS
from roku.discovery import SSDPResponse
from roku.models import Application
from roku.util import serialize_apps


TESTS_PATH = os.path.abspath(os.path.dirname(__file__))


async def test_apps(mocker, async_roku):
    faux_apps = (Application("0x", "1.2.3", "Fauxku Channel Store"),)

    mocked_get = mocker.patch.object(
        AsyncRoku, "_get", new_callable=AsyncMock
    )
    mocked_get.return_value = serialize_apps(faux_apps)

    apps = await async_roku.get_apps()

    assert len(apps) == 1
    assert apps[0].id == "0x"
    assert apps[0].version == "1.2.3"
    assert apps[0].name == "Fauxku Channel Store"


async def test_device_info(mocker, async_roku):
    xml_path = os.path.join(TESTS_PATH, "responses", "device-info.xml")
    with open(xml_path) as infile:
        content = infile.read()

    mocked_get = mocker.patch.object(
        AsyncRoku, "_get", new_callable=AsyncMock
    )
    mocked_get.return_value = content.encode("utf-8")

    d = await async_roku.get_device_info()

    assert d.model_name == "Roku 3"
    assert d.model_num == "4200X"
    assert d.software_version == "7.00.09044"
    assert d.serial_num == "111111111111"
    assert d.roku_type == "Stick"


async def test_media_player(mocker, async_roku):
    xml_path = os.path.join(TESTS_PATH, "responses", "media-player.xml")
    with open(xml_path) as infile:
        content = infile.read()

    mocked_get = mocker.patch.object(
        AsyncRoku, "_get", new_callable=AsyncMock
    )
    mocked_get.return_value = content.encode("utf-8")

    m = await async_roku.get_media_player()

    assert m.state == "pause"
    assert m.app.id == "33"
    assert m.position == 11187
    assert m.duration == 1858000


async def test_commands(async_roku):
    for cmd in async_roku.commands:
        if cmd in ["literal", "search"]:
            continue

        await getattr(async_roku, cmd)()
        call = async_roku.last_call()

        assert call == ("POST", f"/keypress/{COMMANDS[cmd]}", (), {})


async def test_search(async_roku):
    text = "Stargate"
    await async_roku.search(title=text)

    call = async_roku.last_call()

    assert call == ("POST", "/search/browse", (), {"params": {"title": text}})


async def test_literal(async_roku):
    text = "Stargate"
    await async_roku.literal(text)

    for i, call in enumerate(async_roku.calls()):
        assert call == ("POST", f"/keypress/Lit_{quote_plus(text[i])}", (), {})


async def test_literal_fancy(async_roku):
    text = r"""~!@#$%^&*()_+`-=[]{};':",./<>?\|€£"""
    await async_roku.literal(text)

    for i, call in enumerate(async_roku.calls()):
        assert call == ("POST", f"/keypress/Lit_{quote_plus(text[i])}", (), {})


async def test_store(async_roku):
    faux_apps = [
        Application("11", "1.0.1", "Fauxku Channel Store", async_roku),
        Application("22", "2.0.2", "Faux Netflix", async_roku),
    ]
    for app in faux_apps:
        await async_roku.store(app)
        call = async_roku.last_call()

        params = {"params": {"contentID": app.id}}
        assert call == ("POST", "/launch/11", (), params)


async def test_launch(async_roku):
    faux_apps = [
        Application("11", "1.0.1", "Fauxku Channel Store", async_roku),
        Application("22", "2.0.2", "Faux Netflix", async_roku),
    ]
    for app in faux_apps:
        await async_roku.launch(app)
        call = async_roku.last_call()

        params = {"params": {"contentID": app.id}}
        assert call == ("POST", f"/launch/{app.id}", (), params)


async def test_icon_url(async_roku):
    app = Application("11", "1.0.1", "Fauxku Channel Store", async_roku)
    assert async_roku.icon_url(app) == "http://0.0.0.0:8060/query/icon/11"


async def test_context_manager():
    async with AsyncRoku("0.0.0.0") as roku:
        assert roku is not None
        assert roku.host == "0.0.0.0"


async def test_discover():
    class FakeHTTPResponse:
        def getheader(self, name):
            headers = {
                "location": "http://192.168.1.100:8060/",
                "usn": "uuid:roku:ecp:1234",
                "st": "roku:ecp",
                "cache-control": "max-age=3600",
            }
            return headers[name]

    device = SSDPResponse(FakeHTTPResponse())

    with patch(
        "roku._async.core.async_discover", new_callable=AsyncMock
    ) as mock_discover:
        mock_discover.return_value = [device]
        rokus = await AsyncRoku.discover()

    assert len(rokus) == 1
    assert rokus[0].host == "192.168.1.100"
    assert rokus[0].port == 8060
    mock_discover.assert_awaited_once()
