"""
Shared pytest fixtures for all device tests.

Uses tango.test_context.DeviceTestContext to spin up real Tango
device servers in-process — no external Tango DB or network needed.

Usage in a test file::

    def test_something(haadf_proxy):
        haadf_proxy.dwell_time = 2e-6
        assert haadf_proxy.dwell_time == 2e-6
"""

import pytest
from tango.test_context import DeviceTestContext

# Import device classes to test
from src.detectors.HAADF import HAADF
from src.Microscope import Microscope


@pytest.fixture(scope="module")
def haadf_proxy():
    """Live DeviceProxy to a HAADF device running in a test context."""
    with DeviceTestContext(HAADF) as proxy:
        yield proxy


@pytest.fixture(scope="module")
def microscope_proxy():
    """
    Live DeviceProxy to a Microscope device running in a test context.

    Note: AutoScript will not be available in CI — the Microscope device
    detects this and falls back to simulation mode automatically.
    """
    with DeviceTestContext(Microscope) as proxy:
        yield proxy