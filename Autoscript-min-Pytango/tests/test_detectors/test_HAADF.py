"""
Tests for the HAADF detector Tango device.

Runs against a real DeviceTestContext — exercises actual Tango
attribute machinery, not mocks.
"""

import pytest


class TestHAADFAttributes:
    """Attribute read/write round-trips."""

    def test_default_dwell_time(self, haadf_proxy):
        assert haadf_proxy.dwell_time == pytest.approx(1e-6)

    def test_write_dwell_time(self, haadf_proxy):
        haadf_proxy.dwell_time = 5e-6
        assert haadf_proxy.dwell_time == pytest.approx(5e-6)

    def test_default_image_width(self, haadf_proxy):
        assert haadf_proxy.image_width == 1024

    def test_write_image_width(self, haadf_proxy):
        haadf_proxy.image_width = 512
        assert haadf_proxy.image_width == 512

    def test_default_image_height(self, haadf_proxy):
        assert haadf_proxy.image_height == 1024

    def test_write_image_height(self, haadf_proxy):
        haadf_proxy.image_height = 512
        assert haadf_proxy.image_height == 512


class TestHAADFState:
    """Device state checks."""

    def test_initial_state_is_on(self, haadf_proxy):
        import tango
        assert haadf_proxy.state() == tango.DevState.ON