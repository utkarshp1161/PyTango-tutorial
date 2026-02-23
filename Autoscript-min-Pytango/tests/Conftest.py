"""
Shared pytest fixtures for Tango device tests.

Starts BOTH the detector device(s) and the Microscope device in ONE Tango
test device server using MultiDeviceTestContext, so the Microscope can
create DeviceProxy connections to detectors by device name.

This avoids:
- "No proxy found for detector 'haadf'. Available: []"
- Needing a real Tango DB
- Flaky multi-context issues from spinning up multiple separate servers
"""

import pytest
import tango
from tango.test_context import MultiDeviceTestContext

# Import device classes to test
from src.detectors.HAADF import HAADF
from src.Microscope import Microscope as RealMicroscope


# ---- Test-only microscope subclass ----
# Your Microscope._connect_autoscript() currently references self.autoscript_host
# but you only defined autoscript_host_ip/autoscript_host_port.
# In CI you don't want AutoScript anyway, so we bypass it here.
class TestMicroscope(RealMicroscope):
    def _connect_autoscript(self) -> None:
        self.warn_stream("AutoScript disabled in tests (forcing simulation mode)")
        self._microscope = None


@pytest.fixture(scope="module")
def tango_ctx():
    """
    One Tango device server hosting HAADF + Microscope together.

    Device names here MUST match what you put into Microscope properties.
    """
    devices_info = [
        {
            "class": HAADF,
            "devices": [
                {
                    "name": "test/nodb/haadf",
                    "properties": {
                        # put HAADF defaults here if you want
                        # e.g. "dwell_time": 2e-6  (only if it's a device_property)
                    },
                }
            ],
        },
        {
            "class": TestMicroscope,
            "devices": [
                {
                    "name": "test/nodb/microscope",
                    "properties": {
                        # IMPORTANT: address must match the HAADF device name above
                        "haadf_device_address": "test/nodb/haadf",
                        # you can also set these if you later fix autoscript_host usage
                        "autoscript_host_ip": "localhost",
                        "autoscript_host_port": "9090",
                    },
                }
            ],
        },
    ]

    # process=False keeps everything in the same process (fast, debuggable).
    # Also we only create ONE context, so the "second DeviceTestContext segfault"
    # issue doesn't apply.
    ctx = MultiDeviceTestContext(devices_info, process=False)
    with ctx:
        yield ctx


@pytest.fixture(scope="module")
def haadf_proxy(tango_ctx) -> tango.DeviceProxy:
    return tango.DeviceProxy("test/nodb/haadf")


@pytest.fixture(scope="module")
def microscope_proxy(tango_ctx) -> tango.DeviceProxy:
    return tango.DeviceProxy("test/nodb/microscope")