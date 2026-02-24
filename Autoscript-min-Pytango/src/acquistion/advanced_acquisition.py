"""
HAADF (High-Angle Annular Dark-Field) detector Tango device.

This device holds acquisition settings for the HAADF detector.
It does NOT talk to AutoScript directly — the Microscope device
reads these attributes via DeviceProxy before acquiring.
"""

from tango import AttrWriteType, DevState
from tango.server import Device, attribute

class AdvancedAcquisition(Device):
    """Advacned acquisiton settings device."""
    # TODO -----> handle segments

    # ------------------------------------------------------------------
    # Device properties — set per-deployment in the Tango DB
    # ------------------------------------------------------------------

    # (no hardware connection properties needed — HAADF is settings-only)

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------

    dwell_time = attribute(
        label="Dwell Time",
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit="s",
        format="%e",
        min_value=1e-9,
        max_value=1e-6,
        doc="Per-pixel dwell time in seconds (e.g. 1e-6 = 1 µs)",
    )

    base_resolution = attribute(
        label="Image Width",
        dtype=int,
        access=AttrWriteType.READ_WRITE,
        unit="px",
        doc="Acquisition width in pixels (should match an AutoScript ImageSize preset)",
    )

    scan_region = attribute(
        label="Scan Region",
        dtype=(float,),  # Tuple means array of float (returns Python list)
        access=AttrWriteType.READ_WRITE,
        max_dim_x=4,
        doc="Scan region as [x, y, width, height] in relative coordinates,(e.g., top-left corner, 20percent width and 80percent height of the area) ",
    )
    auto_beam_blank = attribute(
        label="Auto Beam Blank",
        dtype=bool,
        access=AttrWriteType.READ_WRITE,
        doc="Automatically blank beam during non-acquisition periods",
    )

    def init_device(self) -> None:
        Device.init_device(self)
        self.set_state(DevState.ON)

        # Sensible defaults
        self._dwell_time: float = 1e-6
        self._base_resolution: int = 1024
        self._scan_region = [0.0, 0.0, 0.2, 0.8]  # (e.g., top-left corner, 20percent width and 80percent height of the area)
        # self._scan_region = [0.0, 0.0, 1, 1]  # full frame

        self._auto_beam_blank: bool = False

        self.info_stream("AdvancedAcquisition device initialised")

    # ------------------------------------------------------------------
    # Attribute read / write
    # ------------------------------------------------------------------

    def read_dwell_time(self) -> float:
        return self._dwell_time

    def write_dwell_time(self, value: float) -> None:
        self._dwell_time = value

    def read_base_resolution(self) -> int:
        return self._base_resolution

    def write_base_resolution(self, value: int) -> None:
        self._base_resolution = value

    def read_scan_region(self):
        return self._scan_region  # Just return the Python list!

    def write_scan_region(self, value):
        self._scan_region = list(value)

    def read_auto_beam_blank(self) -> bool:
        return self._auto_beam_blank

    def write_auto_beam_blank(self, value: bool) -> None:
        self._auto_beam_blank = value


# ----------------------------------------------------------------------
# Server entry point
# ----------------------------------------------------------------------

if __name__ == "__main__":
    AdvancedAcquisition.run_server()