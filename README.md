# python-roku

Screw remotes. Control your [Roku](http://www.roku.com) via Python.

Supports Python 3.10 to 3.14.

## Installation

```
uv add roku
```

or

```
pip install roku
```

To use the async client, install with the `async` extra:

```
uv add "roku[async]"
```

To use the CLI, install with the `cli` extra:

```
uv add "roku[cli]"
```

## Usage

### The Basics

To start, import the Roku object and create it with the IP address or hostname of your Roku.

```python
>>> from roku import Roku
>>> roku = Roku('192.168.10.163')
```

The Roku object has a method for each of the buttons on the remote.

```python
>>> roku.home()
>>> roku.right()
>>> roku.select()
```

To support keyup and keydown events simply pass "keyup" or "keydown" when you call the command.

```python
>>> roku.right("keydown")
>>> roku.right("keyup")
```

To see a full list of available commands, use the *commands* property.

```python
>>> roku.commands
['back', 'backspace', 'down', 'enter', 'forward', 'home', 'info', 'left', 'literal', 'play', 'replay', 'reverse', 'right', 'search', 'select', 'up']
```

If you are following along on your home network and are connected to your Roku, you should see it doing stuff. *Cool!*

### Apps

The *apps* property will return a list of the applications on your device.

```python
>>> roku.apps
[<Application: [2285] Hulu Plus v2.7.6>, <Application: [13] Amazon Instant Video v5.1.3>, <Application: [20445] VEVO v2.0.12092013>]
```

Apps have *id*, *name*, and *version* properties.

```python
>>> app = roku.apps[0]
>>> print(app.id, app.name, app.version)
2285 Hulu Plus 2.7.6
```

You can get an individual app from the Roku object by either its *name* or *id*.

```python
>>> roku['Hulu Plus']
<Application: [2285] Hulu Plus v2.7.6>
>>> roku[2285]
<Application: [2285] Hulu Plus v2.7.6>
```

Seeing the reference to this Hulu Plus app makes me really want to watch the latest episode of [Nashville](http://abc.go.com/shows/nashville). Let's launch it!

```python
>>> hulu = roku['Hulu Plus']
>>> hulu.launch()
```

Again, if you are following along at home, you should see that your Roku has launched the Hulu Plus app. Want to see the app's entry in the Channel Store?

```python
>>> hulu.store()
```

You can also get the app's icon.

```python
>>> with open('hulu.png', 'w') as f:
...     f.write(hulu.icon)

>>> print hulu.icon_url
http://0.0.0.0:8060/query/icon/2285
```

You can get the current running app.

```python
>>> roku.active_app
<Application: [12] Netflix v4.2.75015046>
```

### Entering Text

Okay, I've already seen all of the available episodes of Nashville, so I'm going to search for *Stargate*. With the search open and waiting for text entry:

```python
>>> roku.literal('stargate')
```

What if I now want to watch *The Informant!*? Again, with the search open and waiting for text entry:

```python
>>> roku.literal('The Informant!')
```

This will iterate over each character, sending it individually to the Roku.

## Async

An async client is available for use with `asyncio`. The `AsyncRoku` class provides the same functionality as the synchronous `Roku` class, but with async methods.

```python
>>> import asyncio
>>> from roku._async import AsyncRoku
```

Create an instance and use it as an async context manager:

```python
>>> async def main():
...     async with AsyncRoku('192.168.10.163') as roku:
...         await roku.home()
...         await roku.right()
...         await roku.select()
...
>>> asyncio.run(main())
```

Properties like `apps`, `active_app`, and `device_info` are replaced with async methods:

```python
>>> async def main():
...     async with AsyncRoku('192.168.10.163') as roku:
...         apps = await roku.get_apps()
...         current = await roku.get_active_app()
...         info = await roku.get_device_info()
...
>>> asyncio.run(main())
```

Discovery works as an async class method:

```python
>>> async def main():
...     rokus = await AsyncRoku.discover()
...     for roku in rokus:
...         async with roku:
...             info = await roku.get_device_info()
...             print(info.user_device_name)
...
>>> asyncio.run(main())
```

## CLI

A command-line interface is available for device discovery. Install with the `cli` extra and use the `roku` command:

```
$ roku discover
192.168.10.163:8060
```

Use `-i` / `--inspect` to display device details:

```
$ roku discover -i
192.168.10.163:8060
  Name:     Living Room Roku
  Model:    Roku Ultra (4800X)
  Type:     Box
  Software: 11.5.0.4312
  Serial:   YH009N854321
```

You can adjust the discovery `--timeout` and `--retries`:

```
$ roku discover --timeout 10 --retries 3
```

The CLI also supports the async client with the `--async` flag:

```
$ roku --async discover
```

## Advanced Stuff

### Discovery

Roku devices can be discovered using [SSDP](http://en.wikipedia.org/wiki/Simple_Service_Discovery_Protocol). A class method is available on the Roku object that will return Roku object instances for each device found on the same network.

```python
>>> Roku.discover()
[<Roku: 192.168.10.163:8060>]
```

It may take a few seconds for a device to be found. You can call discover again or change the *timeout* or *retries* parameters on the discover method. This will take longer, but will find more devices.

```python
>>> Roku.discover(timeout=10)
[<Roku: 192.168.10.163:8060>, <Roku: 192.168.10.204:8060>]
```

Thanks to [Dan Krause](https://github.com/dankrause) for his [SSDP code](https://gist.github.com/dankrause/6000248).

### Sensors

Newer Roku remotes have extra sensors built into them that measure acceleration, orientation, and other things. You can mimic these sensors using the provided helper methods.

```python
>>> roku.orientation(1, 1, 1)
```

The parameters to all of the sensor methods are x, y, and z values. Available methods include:

- acceleration - in each dimension relative to free fall measured in meters/sec^2
- magnetic - magnetic field strength in microtesla
- orientation - angular displacement from flat/level and north in radians
- rotation - angular rotation rate about each axis using the right hand rule in radians/sec

### Touch

Some Roku input devices support touch. The parameters to the *touch* method are the *x* and *y* coordinates of the touch.

```python
>>> roku.touch(10, 40)
```

You can change the event triggered by passing an optional *op* parameter.

```python
>>> roku.touch(10, 40, op='up')
```

Supported events are:

- down
- up
- press (down and up)
- move
- cancel

Multitouch is not yet supported in this package.

### Generic Input

Both the sensor and touch methods rely on the generic *input* method for sending data to a running application. If you refuse to use covenience methods because they make people lazy and weak, you can call the sensor and touch methods directly.

```python
>>> params = {'touch.0.x': 10, 'touch.0.y': 20, 'touch.0.op': 'press'}
>>> roku.input(params)
```

More information about input, touch, and sensors is available in the [Roku External Control docs](http://sdkdocs.roku.com/display/sdkdoc/External+Control+Guide#ExternalControlGuide-31ExternalControlInputCommandConventions).

## TODO

- Multitouch support.
- A task runner that will take a set of commands and run them with delays that are appropriate for most devices.
