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
