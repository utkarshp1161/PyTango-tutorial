"""
tango_servers.py

Refactored PyTango device servers for AutoScript microscope.
Architecture: Separate detector devices + main microscope coordinator.

This follows Phase 2B architecture to create clean abstraction over
the single AutoScript microscope object.

Design:
- DetectorDevice: Individual detector with active, dwell_time, resolution, image
- MicroscopeSystemDevice: Main coordinator that manages microscope connection
"""

import time
import numpy as np
from tango import DevState, AttrWriteType
from tango.server import Device, command, attribute


class DetectorDevice(Device):
    """
    Tango device for a single detector.
    
    This device represents one detector (A, B, or C) and provides:
    - Configuration: active, dwell_time, resolution
    - Data acquisition: GetImage command
    - State management
    
    In production, this would wrap AutoScript calls for a specific detector.
    For now, it simulates detector behavior.
    """
    
    
    def init_device(self):
        """Initialize the detector device."""
        # Detector configuration
        self._active = False
        self._dwell_time = 0.1  # seconds per pixel
        self._resolution = 256  # pixels
        
        # Get detector ID from device name (e.g., "detector_A" -> "A")
        self._detector_id = self.get_name().split('/')[-1].split('_')[-1]
        
        # Simulated microscope connection (in production: shared AutoScript client)
        self._microscope_connected = False
        
        self.set_state(DevState.STANDBY)
        self.set_status(f"Detector {self._detector_id} initialized and ready.")
        self.info_stream(f"Detector {self._detector_id} initialized")
    
    # ========================================================================
    # Attributes
    # ========================================================================
    
    @attribute(
        label="Active",
        dtype=bool,
        access=AttrWriteType.READ_WRITE,
        doc="Whether this detector is active and ready for acquisition"
    )
    def active(self):
        return self._active
    
    def write_active(self, value):
        """Activate/deactivate the detector."""
        if value and not self._active:
            self.info_stream(f"Activating detector {self._detector_id}")
            # In production: microscope.imaging.set_active_device(detector_id)
        elif not value and self._active:
            self.info_stream(f"Deactivating detector {self._detector_id}")
        self._active = value
    
    @attribute(
        label="Dwell Time",
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit="s",
        format="%6.3f",
        doc="Dwell time per pixel in seconds"
    )
    def dwell_time(self):
        return self._dwell_time
    
    def write_dwell_time(self, value):
        """Set dwell time (requires detector to be active)."""
        if not self._active:
            raise Exception(
                f"Cannot set dwell_time: detector {self._detector_id} is not active. "
                "Set active = True first."
            )
        if value <= 0:
            raise ValueError("Dwell time must be positive")
        self._dwell_time = value
        self.info_stream(f"Detector {self._detector_id} dwell_time set to {value}s")
    
    @attribute(
        label="Resolution",
        dtype=int,
        access=AttrWriteType.READ_WRITE,
        unit="px",
        doc="Image resolution (width and height in pixels)"
    )
    def resolution(self):
        return self._resolution
    
    def write_resolution(self, value):
        """Set resolution (requires detector to be active)."""
        if not self._active:
            raise Exception(
                f"Cannot set resolution: detector {self._detector_id} is not active. "
                "Set active = True first."
            )
        if value <= 0 or value > 4096:
            raise ValueError("Resolution must be between 1 and 4096")
        self._resolution = value
        self.info_stream(f"Detector {self._detector_id} resolution set to {value}px")
    
    @attribute(
        label="Detector ID",
        dtype=str,
        access=AttrWriteType.READ,
        doc="Detector identifier (A, B, or C)"
    )
    def detector_id(self):
        return self._detector_id
    
    # ========================================================================
    # Commands
    # ========================================================================
    
    @command(dtype_out=[float], doc_out="Flattened image array")
    def GetImage(self):
        """
        Acquire an image from this detector.
        
        Returns:
            Flattened 1D array of image data (reshape to resolution x resolution)
        
        Raises:
            Exception: If detector is not active or acquisition fails
        """
        if not self._active:
            raise Exception(
                f"Detector {self._detector_id} is not active. "
                "Set active = True first."
            )
        
        # Validate acquisition time
        total_time = self._dwell_time * self._resolution * self._resolution
        if total_time > 600:
            raise Exception(
                f"Acquisition too long: {total_time:.1f}s (max 600s). "
                "Reduce dwell_time or resolution."
            )
        
        try:
            # Set state to RUNNING
            self.set_state(DevState.RUNNING)
            self.set_status(
                f"Acquiring {self._resolution}x{self._resolution} image "
                f"from detector {self._detector_id}..."
            )
            self.info_stream(
                f"Acquiring: detector {self._detector_id}, "
                f"{self._resolution}x{self._resolution}, "
                f"{self._dwell_time}s/pixel, total={total_time:.1f}s"
            )
            
            # Simulate acquisition time (in production: actual AutoScript call)
            time.sleep(2)  # Reduced for demo
            
            # Generate simulated image
            # In production: microscope.imaging.grab_frame()
            image = self._generate_simulated_image()
            flattened_image = image.flatten()
            
            # Return to STANDBY state
            self.set_state(DevState.STANDBY)
            self.set_status(f"Detector {self._detector_id} ready.")
            
            self.info_stream(
                f"Returning {len(flattened_image)} pixels "
                f"(reshape to {self._resolution}x{self._resolution})"
            )
            return flattened_image
            
        except Exception as e:
            self.set_state(DevState.FAULT)
            error_msg = f"Image acquisition failed: {str(e)}"
            self.set_status(error_msg)
            self.error_stream(error_msg)
            raise
    
    def _generate_simulated_image(self):
        """Generate a simulated image (digital twin mode)."""
        # Create different patterns for different detectors
        if self._detector_id == 'A':
            # Gradient pattern
            x = np.linspace(0, 1, self._resolution)
            y = np.linspace(0, 1, self._resolution)
            X, Y = np.meshgrid(x, y)
            image = (X + Y) / 2 * 255
        elif self._detector_id == 'B':
            # Circular pattern
            x = np.linspace(-1, 1, self._resolution)
            y = np.linspace(-1, 1, self._resolution)
            X, Y = np.meshgrid(x, y)
            R = np.sqrt(X**2 + Y**2)
            image = (1 - np.clip(R, 0, 1)) * 255
        else:  # C
            # Random noise
            image = np.random.rand(self._resolution, self._resolution) * 255
        
        return image.astype(np.float64)


class MicroscopeSystemDevice(Device):
    """
    Main microscope system coordinator device.
    
    This device manages the overall microscope connection and provides
    system-level commands like Connect and GetStage.
    
    In production, this would own the AutoScript connection and coordinate
    between detector devices.
    """
    
    
    def init_device(self):
        """Initialize the microscope system."""
        # Microscope connection (in production: SdbMicroscopeClient)
        self._microscope = None
        self._connection_string = ""
        
        self.set_state(DevState.INIT)
        self.set_status("Microscope system initialized. Use Connect command.")
        self.info_stream("Microscope system initialized")
    
    # ========================================================================
    # Attributes
    # ========================================================================
    
    @attribute(
        label="Connected",
        dtype=bool,
        access=AttrWriteType.READ,
        doc="Whether microscope is connected"
    )
    def connected(self):
        return self._microscope is not None
    
    @attribute(
        label="Connection String",
        dtype=str,
        access=AttrWriteType.READ,
        doc="Current connection string (host:port)"
    )
    def connection_string(self):
        return self._connection_string
    
    # ========================================================================
    # Commands
    # ========================================================================
    
    @command(
        dtype_in=str,
        dtype_out=str,
        doc_in="Connection string (format: 'host:port')",
        doc_out="Connection status message"
    )
    def Connect(self, connection_string):
        """
        Connect to the microscope.
        
        Args:
            connection_string: Format "host:port" (e.g., "localhost:9001")
            
        Returns:
            Connection status message
        """
        # Parse connection string
        if ":" in connection_string:
            host, port = connection_string.split(":")
            port = int(port)
        else:
            host = connection_string
            port = 9001
        
        try:
            self.info_stream(f"Connecting to microscope at {host}:{port}...")
            
            # In production: self._microscope = SdbMicroscopeClient()
            # In production: self._microscope.connect(host, port)
            self._microscope = 'DigitalTwin'  # Simulated connection
            self._connection_string = f"{host}:{port}"
            
            # Update state
            self.set_state(DevState.ON)
            msg = f"Connected to microscope at {host}:{port}"
            self.set_status(msg)
            
            self.info_stream(msg)
            return msg
            
        except Exception as e:
            self.set_state(DevState.FAULT)
            error_msg = f"Failed to connect: {str(e)}"
            self.set_status(error_msg)
            self.error_stream(error_msg)
            raise
    
    @command(
        dtype_out=[float],
        doc_out="Stage position [x, y, z, tilt, rotation]"
    )
    def GetStage(self):
        """
        Get current stage position.
        
        Returns:
            List of 5 floats: [x, y, z, tilt, rotation]
        """
        if self._microscope is None:
            raise Exception("Microscope not connected. Use Connect command first.")
        
        try:
            # In production: self._microscope.specimen.stage.get_position()
            positions = [np.random.uniform(-10, 10) for _ in range(5)]
            self.info_stream(f"Stage position: {positions}")
            return positions
            
        except Exception as e:
            error_msg = f"Failed to get stage position: {str(e)}"
            self.error_stream(error_msg)
            raise


if __name__ == "__main__":
    # Run both device classes
    # To run: python tango_servers.py detector_A detector_B detector_C microscope
    import sys
    from tango.server import run
    
    classes = {
        'DetectorDevice': DetectorDevice,
        'MicroscopeSystemDevice': MicroscopeSystemDevice,
    }
    
    run(classes)
