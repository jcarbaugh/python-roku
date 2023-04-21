python-roku
===========

Screw remotes. Control your `Roku <http://www.roku.com>`_ via Python.


Installation
------------

::

    pip install roku


Usage
-----


The Basics
~~~~~~~~~~

To start, import the Roku object and create it with the IP address or hostname of your Roku.
::

    >>> from roku import Roku
    >>> roku = Roku('192.168.10.163')

The Roku object has a method for each of the buttons on the remote.
::

    >>> roku.home()
    >>> roku.right()
    >>> roku.select()

To support keyup and keydown events simply pass "keyup" or "keydown" when you call the command.
::

    >>> roku.right("keydown")
    >>> roku.right("keyup")

To see a full list of available commands, use the *commands* property.
::

    >>> roku.commands
    ['back', 'backspace', 'down', 'enter', 'forward', 'home', 'info', 'left', 'literal', 'play', 'replay', 'reverse', 'right', 'search', 'select', 'up']

If you are following along on your home network and are connected to your Roku, you should see it doing stuff. *Cool!*


Apps
~~~~

The *apps* property will return a list of the applications on your device.
::

    >>> roku.apps
    [<Application: [2285] Hulu Plus v2.7.6>, <Application: [13] Amazon Instant Video v5.1.3>, <Application: [20445] VEVO v2.0.12092013>]

Apps have *id*, *name*, and *version* properties.
::

    >>> app = roku.apps[0]
    >>> print(app.id, app.name, app.version)
    2285 Hulu Plus 2.7.6

You can get an individual app from the Roku object by either its *name* or *id*.
::

    >>> roku['Hulu Plus']
    <Application: [2285] Hulu Plus v2.7.6>
    >>> roku[2285]
    <Application: [2285] Hulu Plus v2.7.6>

Seeing the reference to this Hulu Plus app makes me really want to watch the latest episode of `Nashville <http://abc.go.com/shows/nashville>`_. Let's launch it!
::

    >>> hulu = roku['Hulu Plus']
    >>> hulu.launch()

Again, if you are following along at home, you should see that your Roku has launched the Hulu Plus app. Want to see the app's entry in the Channel Store?
::

    >>> hulu.store()

You can also get the app's icon.
::

    >>> with open('hulu.png', 'w') as f:
    ...     f.write(hulu.icon)

    >>> print hulu.icon_url
    http://0.0.0.0:8060/query/icon/2285

You can get the current running app.
::

    >>> roku.active_app
    <Application: [12] Netflix v4.2.75015046>


Entering Text
~~~~~~~~~~~~~

Okay, I've already seen all of the available episodes of Nashville, so I'm going to search for *Stargate*. With the search open and waiting for text entry::

    >>> roku.literal('stargate')

What if I now want to watch *The Informant!*? Again, with the search open and waiting for text entry::

    >>> roku.literal('The Informant!')

This will iterate over each character, sending it individually to the Roku.


Advanced Stuff
--------------


Discovery
~~~~~~~~~

Roku devices can be discovered using `SSDP <http://en.wikipedia.org/wiki/Simple_Service_Discovery_Protocol>`_. A class method is available on the Roku object that will return Roku object instances for each device found on the same network.
::

    >>> Roku.discover()
    [<Roku: 192.168.10.163:8060>]

It may take a few seconds for a device to be found. You can call discover again or change the *timeout* or *retries* parameters on the discover method. This will take longer, but will find more devices.
::

    >>> Roku.discover(timeout=10)
    [<Roku: 192.168.10.163:8060>, <Roku: 192.168.10.204:8060>]

Thanks to `Dan Krause <https://github.com/dankrause>`_ for his `SSDP code <https://gist.github.com/dankrause/6000248>`_.


Sensors
~~~~~~~

Newer Roku remotes have extra sensors built into them that measure acceleration, orientation, and other things.You can mimic these sensors using the provided helper methods.
::

    >>> roku.orientation(1, 1, 1)

The parameters to all of the sensor methods are x, y, and z values. Available methods include:

* acceleration - in each dimension relative to free fall measured in meters/sec^2
* magnetic - magnetic field strength in microtesla
* orientation - angular displacement from flat/level and north in radians
* rotation - angular rotation rate about each axis using the right hand rule in radians/sec


Touch
~~~~~

Some Roku input devices support touch. The parameters to the *touch* method are the *x* and *y* coordinates of the touch.
::

    >>> roku.touch(10, 40)

You can change the event triggered by passing an optional *op* parameter.
::

    >>> roku.touch(10, 40, op='up')

Supported events are:

* down
* up
* press (down and up)
* move
* cancel

Multitouch is not yet supported in this package.

Integrations
~~~~~~~~~~~~
* `pyrokuserve <https://github.com/lingster/pyrokuserve>`_
* `Home Assistant <https://www.home-assistant.io/components/roku/>`_

Generic Input
~~~~~~~~~~~~~

Both the sensor and touch methods rely on the generic *input* method for sending data to a running application. If you refuse to use covenience methods because they make people lazy and weak, you can call the sensor and touch methods directly.
::

    >>> params = {'touch.0.x': 10, 'touch.0.y': 20, 'touch.0.op': 'press'}
    >>> roku.input(params)

More information about input, touch, and sensors is available in the `Roku External Control docs <http://sdkdocs.roku.com/display/sdkdoc/External+Control+Guide#ExternalControlGuide-31ExternalControlInputCommandConventions>`_.


TODO
----

* Tests, of course.
* Multitouch support.
* A Flask proxy server that can listen to requests and forward them to devices on the local network. Control multiple devices at once, eh?
* A server that mimics the Roku interface so you can make your own Roku-like stuff.
* A task runner that will take a set of commands and run them with delays that are appropriate for most devices.
