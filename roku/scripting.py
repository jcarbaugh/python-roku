import logging
import os
import re
import time
from collections import namedtuple

SCRIPT_RE = re.compile(
    r"(?P<command>\w+)(?:\:(?P<param>[\w\s]+))?(?:\@(?P<count>\d+))?(?:\*(?P<sleep>[\d\.]+))?"
)  # noqa

Command = namedtuple("Command", ["command", "param", "count", "sleep"])

logger = logging.getLogger("roku.scripting")


def load_script(path, params=None, raw=False):
    if not os.path.exists(path):
        raise ValueError(f"script at {path} not found")
    with open(path) as infile:
        content = infile.read()
    if params:
        content = content.format(**params)
    if not raw:
        content = content.strip().split("\n")
    return content


def parse_script(script):
    commands = []
    for line in script:
        if not line:
            continue
        m = SCRIPT_RE.match(line)
        if m:
            data = m.groupdict()
            data["count"] = int(data["count"] or 1)
            data["sleep"] = float(data["sleep"]) if data["sleep"] else None
            commands.append(Command(**data))
    return commands


def run_script(roku, script, sleep=0.5):
    for cmd in script:
        logger.debug(cmd)
        for i in range(cmd.count or 1):
            func = getattr(roku, cmd.command)
            if func:
                if cmd.param:
                    func(cmd.param)
                else:
                    func()
                time.sleep(cmd.sleep or sleep)
