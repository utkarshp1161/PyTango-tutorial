"""
Device_AS_twin.py

PyTango device server for AutoScript microscope digital twin.
Clean, simple implementation using PyTango best practices.

Design: Detector parameters (active, dwell_time, resolution) are set via attributes,
        and GetImage() only takes the detector name.

This file is designed to be a learning example - simple and clear!
"""

import time
import numpy as np
from tango import DevState, AttrWriteType, DevVarDoubleArray
from tango.server import Device, command, attribute


class DeviceASTwin(Device):
    """
    PyTango device server for AutoScript microscope digital twin.
    
    This device simulates a microscope with three detectors (A, B, C).
    Each detector can be configured and used to acquire images.
    
    Example usage:
        device.detector_A_active = True
        device.detector_A_dwell_time = 0.1
        device.detector_A_resolution = 256
        image = device.GetImage('detector_A')
    
    States:
        INIT: Device initialized but not connected
        STANDBY: Connected and ready
        RUNNING: Acquiring data
        FAULT: Error condition
    """
    
    # ========================================================================
    # Attribute Declarations (Class Level)
    # ========================================================================
    
    # Detector A
    detector_A_active = attribute(label="Detector A Active", dtype=bool, access=AttrWriteType.READ_WRITE)
    detector_A_dwell_time = attribute(label="Detector A Dwell Time", dtype=float, access=AttrWriteType.READ_WRITE, unit="s", format="%6.3f")
    detector_A_resolution = attribute(label="Detector A Resolution", dtype=int, access=AttrWriteType.READ_WRITE, unit="px")
    
    # Detector B
    detector_B_active = attribute(label="Detector B Active", dtype=bool, access=AttrWriteType.READ_WRITE)
    detector_B_dwell_time = attribute(label="Detector B Dwell Time", dtype=float, access=AttrWriteType.READ_WRITE, unit="s", format="%6.3f")
    detector_B_resolution = attribute(label="Detector B Resolution", dtype=int, access=AttrWriteType.READ_WRITE, unit="px")
    
    # Detector C
    detector_C_active = attribute(label="Detector C Active", dtype=bool, access=AttrWriteType.READ_WRITE)
    detector_C_dwell_time = attribute(label="Detector C Dwell Time", dtype=float, access=AttrWriteType.READ_WRITE, unit="s", format="%6.3f")
    detector_C_resolution = attribute(label="Detector C Resolution", dtype=int, access=AttrWriteType.READ_WRITE, unit="px")
    
    # Microscope status
    microscope_connected = attribute(label="Microscope Connected", dtype=bool, access=AttrWriteType.READ)
    
    # ========================================================================
    # Initialization
    # ========================================================================
    
    def init_device(self):
        """Initialize the device."""
        super().init_device()
        
        # Microscope connection
        self.microscope = None
        
        # Detector A configuration
        self._detector_A_active = False
        self._detector_A_dwell_time = 0.1
        self._detector_A_resolution = 256
        
        # Detector B configuration
        self._detector_B_active = False
        self._detector_B_dwell_time = 0.1
        self._detector_B_resolution = 256
        
        # Detector C configuration
        self._detector_C_active = False
        self._detector_C_dwell_time = 0.1
        self._detector_C_resolution = 256
        
        # Set initial state
        self.set_state(DevState.INIT)
        self.set_status("Device initialized. Use Connect command to connect to microscope.")
    
    # ========================================================================
    # Detector A - Read/Write Methods
    # ========================================================================
    
    def read_detector_A_active(self):
        return self._detector_A_active
    
    def write_detector_A_active(self, value):
        if not self._detector_A_active and value:
            self.info_stream("Activating detector_A")
        self._detector_A_active = value
    
    def read_detector_A_dwell_time(self):
        if not self._detector_A_active:
            self.warn_stream("Reading dwell_time for inactive detector_A")
        return self._detector_A_dwell_time
    
    def write_detector_A_dwell_time(self, value):
        if not self._detector_A_active:
            raise Exception("Cannot set dwell_time: detector_A is not active. Set detector_A_active = True first.")
        self._detector_A_dwell_time = value
        self.info_stream(f"Set detector_A dwell_time to {value}s")
    
    def read_detector_A_resolution(self):
        if not self._detector_A_active:
            self.warn_stream("Reading resolution for inactive detector_A")
        return self._detector_A_resolution
    
    def write_detector_A_resolution(self, value):
        if not self._detector_A_active:
            raise Exception("Cannot set resolution: detector_A is not active. Set detector_A_active = True first.")
        self._detector_A_resolution = value
        self.info_stream(f"Set detector_A resolution to {value}")
    
    # ========================================================================
    # Detector B - Read/Write Methods
    # ========================================================================
    
    def read_detector_B_active(self):
        return self._detector_B_active
    
    def write_detector_B_active(self, value):
        if not self._detector_B_active and value:
            self.info_stream("Activating detector_B")
        self._detector_B_active = value
    
    def read_detector_B_dwell_time(self):
        if not self._detector_B_active:
            self.warn_stream("Reading dwell_time for inactive detector_B")
        return self._detector_B_dwell_time
    
    def write_detector_B_dwell_time(self, value):
        if not self._detector_B_active:
            raise Exception("Cannot set dwell_time: detector_B is not active. Set detector_B_active = True first.")
        self._detector_B_dwell_time = value
        self.info_stream(f"Set detector_B dwell_time to {value}s")
    
    def read_detector_B_resolution(self):
        if not self._detector_B_active:
            self.warn_stream("Reading resolution for inactive detector_B")
        return self._detector_B_resolution
    
    def write_detector_B_resolution(self, value):
        if not self._detector_B_active:
            raise Exception("Cannot set resolution: detector_B is not active. Set detector_B_active = True first.")
        self._detector_B_resolution = value
        self.info_stream(f"Set detector_B resolution to {value}")
    
    # ========================================================================
    # Detector C - Read/Write Methods
    # ========================================================================
    
    def read_detector_C_active(self):
        return self._detector_C_active
    
    def write_detector_C_active(self, value):
        if not self._detector_C_active and value:
            self.info_stream("Activating detector_C")
        self._detector_C_active = value
    
    def read_detector_C_dwell_time(self):
        if not self._detector_C_active:
            self.warn_stream("Reading dwell_time for inactive detector_C")
        return self._detector_C_dwell_time
    
    def write_detector_C_dwell_time(self, value):
        if not self._detector_C_active:
            raise Exception("Cannot set dwell_time: detector_C is not active. Set detector_C_active = True first.")
        self._detector_C_dwell_time = value
        self.info_stream(f"Set detector_C dwell_time to {value}s")
    
    def read_detector_C_resolution(self):
        if not self._detector_C_active:
            self.warn_stream("Reading resolution for inactive detector_C")
        return self._detector_C_resolution
    
    def write_detector_C_resolution(self, value):
        if not self._detector_C_active:
            raise Exception("Cannot set resolution: detector_C is not active. Set detector_C_active = True first.")
        self._detector_C_resolution = value
        self.info_stream(f"Set detector_C resolution to {value}")
    
    # ========================================================================
    # Other Attributes - Read Methods
    # ========================================================================
    
    def read_microscope_connected(self):
        return self.microscope is not None
    
    # ========================================================================
    # Commands
    # ========================================================================
    
    @command(dtype_in=str, dtype_out=str)
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
            
            # Digital twin mode - simulate connection
            self.microscope = 'Debugging'
            
            # Update state
            self.set_state(DevState.STANDBY)
            msg = f"Connected to Digital Twin microscope at {host}:{port}"
            self.set_status(msg)
            
            self.info_stream(msg)
            return msg
            
        except Exception as e:
            self.set_state(DevState.FAULT)
            error_msg = f"Failed to connect: {str(e)}"
            self.set_status(error_msg)
            self.error_stream(error_msg)
            raise
    # @command(dtype_in=str, dtype_out=DevVarDoubleArray)
    @command(dtype_in=str, dtype_out=[float])
    def GetImage(self, detector_name):
        """
        Acquire an image from the specified detector.
        
        Args:
            detector_name: Name of detector ('detector_A', 'detector_B', or 'detector_C')
            
        Returns:
            Flattened 1D array of image data (reshape on client side using resolution)
        """
        if self.microscope is None:
            raise Exception("Microscope not connected. Use Connect command first.")
        
        # Get detector configuration based on name
        if detector_name == 'detector_A':
            active = self._detector_A_active
            dwell_time = self._detector_A_dwell_time
            resolution = self._detector_A_resolution
        elif detector_name == 'detector_B':
            active = self._detector_B_active
            dwell_time = self._detector_B_dwell_time
            resolution = self._detector_B_resolution
        elif detector_name == 'detector_C':
            active = self._detector_C_active
            dwell_time = self._detector_C_dwell_time
            resolution = self._detector_C_resolution
        else:
            raise Exception(f"Unknown detector: {detector_name}. Use 'detector_A', 'detector_B', or 'detector_C'.")
        
        # Check if detector is active
        if not active:
            raise Exception(f"Detector {detector_name} is not active. Set {detector_name}_active = True first.")
        
        # Validate acquisition time (max 10 minutes)
        total_time = dwell_time * resolution * resolution
        if total_time > 600:
            raise Exception(f"Acquisition too long: {total_time:.1f}s (max 600s). Reduce dwell_time or resolution.")
        
        try:
            # Set state to RUNNING
            self.set_state(DevState.RUNNING)
            self.set_status(f"Acquiring {resolution}x{resolution} image from {detector_name}...")
            self.info_stream(f"Acquiring: {detector_name}, {resolution}x{resolution}, {dwell_time}s/pixel, total={total_time:.1f}s")
            
            # Simulate acquisition time
            time.sleep(5)
            
            # Generate random image (digital twin simulation)
            image = (np.random.rand(resolution, resolution) * 255).astype(np.float64)
            flattened_image = image.flatten()
            
            # Return to STANDBY state
            self.set_state(DevState.STANDBY)
            self.set_status("Image acquisition complete. Ready for next command.")
            
            self.info_stream(f"Returning {len(flattened_image)} pixels (reshape to {resolution}x{resolution})")
            return flattened_image
            
        except Exception as e:
            self.set_state(DevState.FAULT)
            error_msg = f"Image acquisition failed: {str(e)}"
            self.set_status(error_msg)
            self.error_stream(error_msg)
            raise
    
    @command(dtype_out=[float])
    def GetStage(self):
        """
        Get current stage position.
        
        Returns:
            List of 5 floats: [x, y, z, tilt, rotation]
        """
        if self.microscope is None:
            raise Exception("Microscope not connected. Use Connect command first.")
        
        try:
            # Generate random stage positions (digital twin simulation)
            positions = [np.random.uniform(-10, 10) for _ in range(5)]
            self.info_stream(f"Stage position: {positions}")
            return positions
            
        except Exception as e:
            error_msg = f"Failed to get stage position: {str(e)}"
            self.error_stream(error_msg)
            raise


if __name__ == "__main__":
    DeviceASTwin.run_server()
