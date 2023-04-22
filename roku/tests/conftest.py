import pytest

from roku import Application, Roku


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
