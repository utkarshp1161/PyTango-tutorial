"""
Microscope Tango device.

Owns the AutoScript connection and all acquisition commands.
Detector settings are read from the corresponding detector DeviceProxy
so that each detector device is the single source of truth for its own params.

Return convention for image commands
-------------------------------------
All image commands return DevEncoded = (str, bytes) where:
  - str  : JSON string containing metadata (shape, dtype, dwell_time, …)
  - bytes: raw numpy array bytes (reconstruct with np.frombuffer + reshape)

Client-side reconstruction example::

    import json, numpy as np
    encoded = proxy.get_haadf_image()   # returns (json_str, raw_bytes)
    meta    = json.loads(encoded[0])
    image   = np.frombuffer(encoded[1], dtype=meta["dtype"]).reshape(meta["shape"])
"""

import json
import time
from typing import Optional

import numpy as np
import tango
from tango import AttrWriteType, DevEncoded, DevState
from tango.server import Device, attribute, command, device_property

# AutoScript imports — only available on the microscope PC.
# Wrapped in try/except so the device can still be imported and tested
# on a development machine without AutoScript installed.
try:
    from autoscript_tem_microscope_client import TemMicroscopeClient
    from autoscript_tem_microscope_client.enumerations import DetectorType, ImageSize
    _AUTOSCRIPT_AVAILABLE = True
except ImportError:
    _AUTOSCRIPT_AVAILABLE = False


class Microscope(Device):
    """
    Top-level TEM microscope device.

    Manages the AutoScript connection and exposes acquisition commands.
    Detector-specific settings (dwell time, resolution) are stored in
    dedicated detector devices and read via DeviceProxy at acquisition time.
    """

    # ------------------------------------------------------------------
    # Device properties — configure in Tango DB per deployment
    # ------------------------------------------------------------------

    autoscript_host_ip = device_property(
        dtype=str,
        default_value="localhost",
        doc="Hostname or IP of the AutoScript microscope server",
    )

    autoscript_host_port = device_property(
        dtype=str,
        default_value="9090",
        doc="Hostname or IP of the AutoScript microscope server",
    )

    haadf_device_address = device_property(
        dtype=str,
        doc="Tango device address for the HAADF settings device. "
            "DB mode: 'test/detector/haadf' "
            "No-DB mode: 'tango://127.0.0.1:8888/test/nodb/haadf#dbase=no'",
)

    # Add further detector device_property entries here as detectors are added
    # eds_device_address   = device_property(dtype=str, default_value="test/detector/eds")
    # eels_device_address  = device_property(dtype=str, default_value="test/detector/eels")

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------

    stem_mode = attribute(
        label="STEM Mode",
        dtype=bool,
        access=AttrWriteType.READ,
        doc="True when the microscope is in STEM mode",
    )

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def init_device(self) -> None:
        Device.init_device(self)
        self.set_state(DevState.INIT)

        self._microscope: Optional[object] = None  # TemMicroscopeClient instance
        self._stem_mode: bool = False

        # Dict mapping detector name string → DeviceProxy
        # Populated in _connect_detector_proxies
        self._detector_proxies: dict[str, tango.DeviceProxy] = {}

        self._connect()

    def _connect(self) -> None:
        """Connect to AutoScript and set up detector proxies."""
        self._connect_autoscript()
        self._connect_detector_proxies()
        self.set_state(DevState.ON)

    def _connect_autoscript(self) -> None:
        """Establish AutoScript connection."""
        if not _AUTOSCRIPT_AVAILABLE:
            self.warn_stream("AutoScript not available — running in simulation mode")
            return
        try:
            self._microscope = TemMicroscopeClient()
            self._microscope.connect(self.autoscript_host)
            self.info_stream(f"Connected to AutoScript at {self.autoscript_host}")
        except Exception as e:
            self.error_stream(f"AutoScript connection failed: {e}")
            self.set_state(DevState.FAULT)

    def _connect_detector_proxies(self) -> None:
        """Build DeviceProxy objects for each configured detector device."""
        # Extend this dict as more detectors are added
        addresses: dict[str, str] = {
            "haadf": self.haadf_device_address,
            # "eds":  self.eds_device_address,
        }
        for name, address in addresses.items():
            try:
                self._detector_proxies[name] = tango.DeviceProxy(address)
                self.info_stream(f"Connected to detector proxy: {name} @ {address}")
            except tango.DevFailed as e:
                self.error_stream(f"Failed to connect to {name} proxy at {address}: {e}")

    # ------------------------------------------------------------------
    # Attribute read methods
    # ------------------------------------------------------------------

    def read_stem_mode(self) -> bool:
        # TODO: query self._microscope.optics.mode when AutoScript available
        return self._stem_mode

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    @command
    def Connect(self) -> None:
        """Explicitly (re)connect to AutoScript. Useful after a fault."""
        self._connect()

    @command
    def Disconnect(self) -> None:
        """Disconnect from AutoScript gracefully."""
        # TODO: self._microscope.disconnect() when AutoScript available
        self._microscope = None
        self.set_state(DevState.OFF)
        self.info_stream("Disconnected from AutoScript")

    @command(dtype_in=str, dtype_out=DevEncoded)
    def get_image(self, detector_name: str) -> tuple[str, bytes]:
        """
        Acquire a single STEM image from the named detector.

        Parameters
        ----------
        detector_name:
            Name of the detector, e.g. "haadf". Must match a key in
            self._detector_proxies.

        Returns
        -------
        DevEncoded = (json_metadata, raw_bytes)
            json_metadata includes: shape, dtype, dwell_time, detector,
            timestamp, and any other relevant metadata.
            raw_bytes is the flat numpy array bytes; reshape using shape from metadata.
        """
        detector_name = detector_name.lower().strip()

        proxy = self._detector_proxies.get(detector_name)
        if proxy is None:
            tango.Except.throw_exception(
                "UnknownDetector",
                f"No proxy found for detector '{detector_name}'. "
                f"Available: {list(self._detector_proxies.keys())}",
                "Microscope.get_image()",
            )

        # Read acquisition settings from the detector device
        dwell_time: float = proxy.dwell_time
        width: int  = proxy.image_width
        height: int = proxy.image_height

        # TODO: map (width, height) → AutoScript ImageSize enum
        # e.g. ImageSize.PRESET_1024 when width == height == 1024

        adorned_image = self._acquire_stem_image(detector_name, width, height, dwell_time)

        metadata = {
            "detector": detector_name,
            "shape": [height, width],
            "dtype": str(adorned_image.dtype),
            "dwell_time": dwell_time,
            "timestamp": time.time(),
            # TODO: add metadata from adorned_image.metadata when using real AutoScript
        }

        return json.dumps(metadata), adorned_image.tobytes()

    # ------------------------------------------------------------------
    # Internal acquisition helpers
    # ------------------------------------------------------------------

    def _acquire_stem_image(
        self,
        detector_name: str,
        width: int,
        height: int,
        dwell_time: float,
    ) -> np.ndarray:
        """
        Call AutoScript acquisition and return numpy array.

        Falls back to a simulated image when AutoScript is unavailable.
        """
        if self._microscope is not None:
            # Real AutoScript path
            # detector_type = DetectorType[detector_name.upper()]
            # adorned = self._microscope.acquisition.acquire_stem_image(
            #     detector_type, ImageSize.PRESET_1024, dwell_time
            # )
            # return adorned.data
            pass  # remove this line when uncommenting above

        # Simulation fallback
        self.warn_stream("Simulating image acquisition (AutoScript not connected)")
        rng = np.random.default_rng()
        return rng.integers(0, 65535, size=(height, width), dtype=np.uint16)


# ----------------------------------------------------------------------
# Server entry point
# ----------------------------------------------------------------------

if __name__ == "__main__":
    Microscope.run_server()