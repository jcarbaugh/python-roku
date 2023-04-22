import pytest

from roku import scripting


SCRIPT_PATH = "roku/tests/scripts/testscript.txt"


def test_loading():
    scripting.load_script(SCRIPT_PATH)


def test_loading_params():
    params = {
        "avar": "here",
        "notavar": "missing",
    }
    content = scripting.load_script(SCRIPT_PATH, params=params, raw=True)
    assert "literal:here" in content
    assert "literal:missing" not in content


def test_loading_notfound():
    with pytest.raises(ValueError):
        scripting.load_script("thisisnotarealscript.txt")


def test_parse_command_only():
    content = ("home",)
    script = scripting.parse_script(content)
    command = script[0]
    assert command == scripting.Command("home", None, 1, None)


def test_parse_command_param():
    content = ("literal:barbecue",)
    script = scripting.parse_script(content)
    command = script[0]
    assert command == scripting.Command("literal", "barbecue", 1, None)


def test_parse_command_count():
    content = ("left@10",)
    script = scripting.parse_script(content)
    command = script[0]
    assert command == scripting.Command("left", None, 10, None)


def test_parse_command_sleep():
    content = ("left*2",)
    script = scripting.parse_script(content)
    command = script[0]
    assert command == scripting.Command("left", None, 1, 2.0)


def test_parse_command_all():
    content = ("literal:barbecue@3*5.1",)
    script = scripting.parse_script(content)
    command = script[0]
    assert command == scripting.Command("literal", "barbecue", 3, 5.1)


def test_run_script(roku):
    content = ("home", "literal:x")
    script = scripting.parse_script(content)
    scripting.run_script(roku, script)
    calls = roku.calls()
    assert "keypress/Home" in calls[0][1]
    assert "keypress/Lit_x" in calls[1][1]
