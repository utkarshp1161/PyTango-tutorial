# SPDX-FileCopyrightText: All Contributors to the PyTango project
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Demo Tango Device Server using gevent green mode"""

import gevent
from tango import DevState, GreenMode
from tango.server import Device, command, attribute

class GeventDevice(Device):
    # Enable the Gevent green mode
    green_mode = GreenMode.Gevent

    def init_device(self):
        """Standard initialization. No 'async' keyword needed."""
        super().init_device()
        self.set_state(DevState.ON)

    @command
    def long_running_command(self):
        """Standard method that becomes non-blocking via gevent.sleep"""
        self.set_state(DevState.OPEN)
        # Use gevent.sleep instead of asyncio.sleep or time.sleep
        gevent.sleep(2)
        self.set_state(DevState.CLOSE)

    @command
    def background_task_command(self):
        """Spawns a greenlet to run in the background"""
        gevent.spawn(self.coroutine_target)

    def coroutine_target(self):
        """The background work logic"""
        self.set_state(DevState.INSERT)
        gevent.sleep(15)
        self.set_state(DevState.EXTRACT)

    @attribute
    def test_attribute(self):
        """Attributes are processed concurrently without 'await'"""
        gevent.sleep(2)
        return 42

if __name__ == "__main__":
    GeventDevice.run_server()