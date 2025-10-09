"""
Blackmagic DeckLink Output Library

A Python library for outputting video frames to Blackmagic DeckLink devices.
Supports static frame output from NumPy arrays.
"""

import numpy as np
from typing import Optional, Tuple, List
from enum import Enum

try:
    import decklink_output as _decklink
except ImportError:
    raise ImportError(
        "DeckLink output module not found. Please build the C++ extension first. "
        "Run: python setup.py build_ext --inplace"
    )


class Matrix(Enum):
    """RGB to Y'CbCr conversion matrix"""
    Rec709 = _decklink.Gamut.Rec709
    Rec2020 = _decklink.Gamut.Rec2020


class Eotf(Enum):
    """Electro-Optical Transfer Function for HDR"""
    SDR = _decklink.Eotf.SDR
    PQ = _decklink.Eotf.PQ
    HLG = _decklink.Eotf.HLG


class PixelFormat(Enum):
    """Supported pixel formats for DeckLink output"""
    YUV = _decklink.PixelFormat.YUV
    BGRA = _decklink.PixelFormat.BGRA
    YUV10 = _decklink.PixelFormat.YUV10


class DisplayMode(Enum):
    """Supported display modes for DeckLink output"""
    # SD Modes
    NTSC = _decklink.DisplayMode.NTSC
    NTSC2398 = _decklink.DisplayMode.NTSC2398
    PAL = _decklink.DisplayMode.PAL
    NTSCp = _decklink.DisplayMode.NTSCp
    PALp = _decklink.DisplayMode.PALp

    # HD 1080 Progressive
    HD1080p2398 = _decklink.DisplayMode.HD1080p2398
    HD1080p24 = _decklink.DisplayMode.HD1080p24
    HD1080p25 = _decklink.DisplayMode.HD1080p25
    HD1080p2997 = _decklink.DisplayMode.HD1080p2997
    HD1080p30 = _decklink.DisplayMode.HD1080p30
    HD1080p4795 = _decklink.DisplayMode.HD1080p4795
    HD1080p48 = _decklink.DisplayMode.HD1080p48
    HD1080p50 = _decklink.DisplayMode.HD1080p50
    HD1080p5994 = _decklink.DisplayMode.HD1080p5994
    HD1080p60 = _decklink.DisplayMode.HD1080p60
    HD1080p9590 = _decklink.DisplayMode.HD1080p9590
    HD1080p96 = _decklink.DisplayMode.HD1080p96
    HD1080p100 = _decklink.DisplayMode.HD1080p100
    HD1080p11988 = _decklink.DisplayMode.HD1080p11988
    HD1080p120 = _decklink.DisplayMode.HD1080p120

    # HD 1080 Interlaced
    HD1080i50 = _decklink.DisplayMode.HD1080i50
    HD1080i5994 = _decklink.DisplayMode.HD1080i5994
    HD1080i60 = _decklink.DisplayMode.HD1080i60

    # HD 720
    HD720p50 = _decklink.DisplayMode.HD720p50
    HD720p5994 = _decklink.DisplayMode.HD720p5994
    HD720p60 = _decklink.DisplayMode.HD720p60

    # 2K
    Mode2k2398 = _decklink.DisplayMode.Mode2k2398
    Mode2k24 = _decklink.DisplayMode.Mode2k24
    Mode2k25 = _decklink.DisplayMode.Mode2k25

    # 2K DCI
    Mode2kDCI2398 = _decklink.DisplayMode.Mode2kDCI2398
    Mode2kDCI24 = _decklink.DisplayMode.Mode2kDCI24
    Mode2kDCI25 = _decklink.DisplayMode.Mode2kDCI25
    Mode2kDCI2997 = _decklink.DisplayMode.Mode2kDCI2997
    Mode2kDCI30 = _decklink.DisplayMode.Mode2kDCI30
    Mode2kDCI4795 = _decklink.DisplayMode.Mode2kDCI4795
    Mode2kDCI48 = _decklink.DisplayMode.Mode2kDCI48
    Mode2kDCI50 = _decklink.DisplayMode.Mode2kDCI50
    Mode2kDCI5994 = _decklink.DisplayMode.Mode2kDCI5994
    Mode2kDCI60 = _decklink.DisplayMode.Mode2kDCI60
    Mode2kDCI9590 = _decklink.DisplayMode.Mode2kDCI9590
    Mode2kDCI96 = _decklink.DisplayMode.Mode2kDCI96
    Mode2kDCI100 = _decklink.DisplayMode.Mode2kDCI100
    Mode2kDCI11988 = _decklink.DisplayMode.Mode2kDCI11988
    Mode2kDCI120 = _decklink.DisplayMode.Mode2kDCI120

    # 4K UHD
    Mode4K2160p2398 = _decklink.DisplayMode.Mode4K2160p2398
    Mode4K2160p24 = _decklink.DisplayMode.Mode4K2160p24
    Mode4K2160p25 = _decklink.DisplayMode.Mode4K2160p25
    Mode4K2160p2997 = _decklink.DisplayMode.Mode4K2160p2997
    Mode4K2160p30 = _decklink.DisplayMode.Mode4K2160p30
    Mode4K2160p4795 = _decklink.DisplayMode.Mode4K2160p4795
    Mode4K2160p48 = _decklink.DisplayMode.Mode4K2160p48
    Mode4K2160p50 = _decklink.DisplayMode.Mode4K2160p50
    Mode4K2160p5994 = _decklink.DisplayMode.Mode4K2160p5994
    Mode4K2160p60 = _decklink.DisplayMode.Mode4K2160p60
    Mode4K2160p9590 = _decklink.DisplayMode.Mode4K2160p9590
    Mode4K2160p96 = _decklink.DisplayMode.Mode4K2160p96
    Mode4K2160p100 = _decklink.DisplayMode.Mode4K2160p100
    Mode4K2160p11988 = _decklink.DisplayMode.Mode4K2160p11988
    Mode4K2160p120 = _decklink.DisplayMode.Mode4K2160p120

    # 4K DCI
    Mode4kDCI2398 = _decklink.DisplayMode.Mode4kDCI2398
    Mode4kDCI24 = _decklink.DisplayMode.Mode4kDCI24
    Mode4kDCI25 = _decklink.DisplayMode.Mode4kDCI25
    Mode4kDCI2997 = _decklink.DisplayMode.Mode4kDCI2997
    Mode4kDCI30 = _decklink.DisplayMode.Mode4kDCI30
    Mode4kDCI4795 = _decklink.DisplayMode.Mode4kDCI4795
    Mode4kDCI48 = _decklink.DisplayMode.Mode4kDCI48
    Mode4kDCI50 = _decklink.DisplayMode.Mode4kDCI50
    Mode4kDCI5994 = _decklink.DisplayMode.Mode4kDCI5994
    Mode4kDCI60 = _decklink.DisplayMode.Mode4kDCI60
    Mode4kDCI9590 = _decklink.DisplayMode.Mode4kDCI9590
    Mode4kDCI96 = _decklink.DisplayMode.Mode4kDCI96
    Mode4kDCI100 = _decklink.DisplayMode.Mode4kDCI100
    Mode4kDCI11988 = _decklink.DisplayMode.Mode4kDCI11988
    Mode4kDCI120 = _decklink.DisplayMode.Mode4kDCI120

    # 8K UHD
    Mode8K4320p2398 = _decklink.DisplayMode.Mode8K4320p2398
    Mode8K4320p24 = _decklink.DisplayMode.Mode8K4320p24
    Mode8K4320p25 = _decklink.DisplayMode.Mode8K4320p25
    Mode8K4320p2997 = _decklink.DisplayMode.Mode8K4320p2997
    Mode8K4320p30 = _decklink.DisplayMode.Mode8K4320p30
    Mode8K4320p4795 = _decklink.DisplayMode.Mode8K4320p4795
    Mode8K4320p48 = _decklink.DisplayMode.Mode8K4320p48
    Mode8K4320p50 = _decklink.DisplayMode.Mode8K4320p50
    Mode8K4320p5994 = _decklink.DisplayMode.Mode8K4320p5994
    Mode8K4320p60 = _decklink.DisplayMode.Mode8K4320p60

    # 8K DCI
    Mode8kDCI2398 = _decklink.DisplayMode.Mode8kDCI2398
    Mode8kDCI24 = _decklink.DisplayMode.Mode8kDCI24
    Mode8kDCI25 = _decklink.DisplayMode.Mode8kDCI25
    Mode8kDCI2997 = _decklink.DisplayMode.Mode8kDCI2997
    Mode8kDCI30 = _decklink.DisplayMode.Mode8kDCI30
    Mode8kDCI4795 = _decklink.DisplayMode.Mode8kDCI4795
    Mode8kDCI48 = _decklink.DisplayMode.Mode8kDCI48
    Mode8kDCI50 = _decklink.DisplayMode.Mode8kDCI50
    Mode8kDCI5994 = _decklink.DisplayMode.Mode8kDCI5994
    Mode8kDCI60 = _decklink.DisplayMode.Mode8kDCI60

    # PC Modes
    Mode640x480p60 = _decklink.DisplayMode.Mode640x480p60
    Mode800x600p60 = _decklink.DisplayMode.Mode800x600p60
    Mode1440x900p50 = _decklink.DisplayMode.Mode1440x900p50
    Mode1440x900p60 = _decklink.DisplayMode.Mode1440x900p60
    Mode1440x1080p50 = _decklink.DisplayMode.Mode1440x1080p50
    Mode1440x1080p60 = _decklink.DisplayMode.Mode1440x1080p60
    Mode1600x1200p50 = _decklink.DisplayMode.Mode1600x1200p50
    Mode1600x1200p60 = _decklink.DisplayMode.Mode1600x1200p60
    Mode1920x1200p50 = _decklink.DisplayMode.Mode1920x1200p50
    Mode1920x1200p60 = _decklink.DisplayMode.Mode1920x1200p60
    Mode1920x1440p50 = _decklink.DisplayMode.Mode1920x1440p50
    Mode1920x1440p60 = _decklink.DisplayMode.Mode1920x1440p60
    Mode2560x1440p50 = _decklink.DisplayMode.Mode2560x1440p50
    Mode2560x1440p60 = _decklink.DisplayMode.Mode2560x1440p60
    Mode2560x1600p50 = _decklink.DisplayMode.Mode2560x1600p50
    Mode2560x1600p60 = _decklink.DisplayMode.Mode2560x1600p60


class BlackmagicOutput:
    """
    Main interface for outputting video to Blackmagic DeckLink devices.
    
    Example:
        >>> output = BlackmagicOutput()
        >>> output.initialize(device_index=0)
        >>> frame_data = np.zeros((1080, 1920, 3), dtype=np.uint8)  # Black frame
        >>> output.display_static_frame(frame_data, DisplayMode.HD1080p25)
        >>> output.stop()
    """
    
    def __init__(self):
        self._device = _decklink.DeckLinkOutput()
        self._initialized = False
        self._output_started = False
        self._current_settings = None
        self._current_matrix = Matrix.Rec709

    def initialize(self, device_index: int = 0) -> bool:
        """
        Initialize the DeckLink device.
        
        Args:
            device_index: Index of the DeckLink device to use (default: 0)
            
        Returns:
            True if initialization successful, False otherwise
        """
        if self._device.initialize(device_index):
            self._initialized = True
            return True
        return False

    def get_available_devices(self) -> List[str]:
        """
        Get list of available DeckLink devices.
        
        Returns:
            List of device names
        """
        return self._device.get_device_list()

    def setup_output(self, display_mode: DisplayMode,
                    pixel_format: PixelFormat = PixelFormat.YUV10) -> bool:
        """
        Setup video output parameters.

        Args:
            display_mode: Video resolution and frame rate
            pixel_format: Pixel format (default: YUV10)

        Returns:
            True if setup successful, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Device not initialized. Call initialize() first.")
        
        settings = self._device.get_video_settings(display_mode.value)
        settings.format = pixel_format.value
        
        if self._device.setup_output(settings):
            self._current_settings = settings
            return True
        return False

    def display_static_frame(self, frame_data: np.ndarray,
                           display_mode: DisplayMode,
                           pixel_format: PixelFormat = PixelFormat.YUV10,
                           matrix: Optional[Matrix] = None,
                           hdr_metadata: Optional[dict] = None) -> bool:
        """
        Display a static frame continuously.

        Args:
            frame_data: NumPy array containing image data
                       - For RGB: shape should be (height, width, 3)
                       - For BGRA: shape should be (height, width, 4)
            display_mode: Video resolution and frame rate
            pixel_format: Pixel format (default: YUV10, auto-detected as BGRA for uint8 data)
            matrix: RGB to Y'CbCr conversion matrix (Rec709 or Rec2020).
                   Only applies when pixel_format is YUV10. Default: Rec709
            hdr_metadata: Optional HDR metadata dict with keys:
                         - 'eotf': Eotf enum value (SDR, PQ, or HLG)
                         - 'custom': Optional HdrMetadataCustom object
                         If only eotf is provided, default metadata values are used.

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            if not self.initialize():
                return False

        # Auto-detect pixel format based on dtype if using default YUV10
        # uint8 data should use 8-bit BGRA output, not 10-bit YUV
        if pixel_format == PixelFormat.YUV10 and frame_data.dtype == np.uint8:
            pixel_format = PixelFormat.BGRA

        # Set default matrix if not provided
        if matrix is None:
            matrix = Matrix.Rec709

        # Store matrix for use in update_frame
        self._current_matrix = matrix

        # Handle HDR metadata if provided
        if hdr_metadata is not None:
            eotf = hdr_metadata.get('eotf')
            if eotf is None:
                raise ValueError("hdr_metadata must contain 'eotf' key")

            custom = hdr_metadata.get('custom')
            # Get the internal Gamut value from the Matrix enum
            gamut = matrix.value

            if custom is not None:
                self._device.set_hdr_metadata_custom(gamut, eotf.value, custom)
            else:
                self._device.set_hdr_metadata(gamut, eotf.value)

        # Setup output if not already done or settings changed
        if (not self._current_settings or
            self._current_settings.mode != display_mode.value or
            self._current_settings.format != pixel_format.value):
            if not self.setup_output(display_mode, pixel_format):
                return False

        # Convert frame data if necessary
        processed_frame = self._prepare_frame_data(frame_data, pixel_format, matrix)

        # Set frame data
        if not self._device.set_frame_data(processed_frame):
            return False

        # Start output if not already started
        if not self._output_started:
            if self._device.start_output():
                self._output_started = True
                return True
            return False
        
        return True

    def display_solid_color(self, color: Tuple,
                          display_mode: DisplayMode) -> bool:
        """
        Display a solid color frame continuously.

        Args:
            color: RGB color tuple (r, g, b) with values:
                   - 0-255 for int values (uint8)
                   - 0.0-1.0 for float values (float32)
            display_mode: Video resolution and frame rate

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            if not self.initialize():
                return False

        if not self.setup_output(display_mode):
            return False

        settings = self._current_settings

        # Check if color values are floats
        if isinstance(color[0], float):
            # Create frame as float32 (0.0-1.0 range)
            frame_data = np.full((settings.height, settings.width, 3),
                               color, dtype=np.float32)
            return self.display_static_frame(frame_data, display_mode)
        else:
            # Use existing uint8 path
            frame_data = _decklink.create_solid_color_frame(
                settings.width, settings.height, color
            )
            return self.display_static_frame(frame_data, display_mode, PixelFormat.BGRA)

    def update_frame(self, frame_data: np.ndarray) -> bool:
        """
        Update the currently displayed frame with new data.
        
        Args:
            frame_data: NumPy array containing new image data
            
        Returns:
            True if successful, False otherwise
        """
        if not self._output_started:
            raise RuntimeError("Output not started. Call display_static_frame() first.")

        # Determine pixel format from current settings
        if self._current_settings.format == _decklink.PixelFormat.BGRA:
            pixel_format = PixelFormat.BGRA
        elif self._current_settings.format == _decklink.PixelFormat.YUV10:
            pixel_format = PixelFormat.YUV10
        else:
            pixel_format = PixelFormat.YUV

        processed_frame = self._prepare_frame_data(frame_data, pixel_format, self._current_matrix)

        return self._device.set_frame_data(processed_frame)

    def stop(self, send_black_frame: bool = False) -> bool:
        """
        Stop video output.

        Args:
            send_black_frame: If True, send a black frame before stopping to avoid
                            flickering or frozen last frame. Default: False

        Returns:
            True if successful, False otherwise
        """
        if self._output_started:
            result = self._device.stop_output(send_black_frame)
            self._output_started = False
            return result
        return True

    def cleanup(self, send_black_frame: bool = False):
        """
        Cleanup resources and stop output.

        Args:
            send_black_frame: If True, send a black frame before stopping. Default: False
        """
        self.stop(send_black_frame)
        self._device.cleanup()
        self._initialized = False

    def _prepare_frame_data(self, frame_data: np.ndarray,
                          pixel_format: PixelFormat,
                          matrix: Matrix = Matrix.Rec709) -> np.ndarray:
        """
        Prepare frame data for output, converting format if necessary.

        Args:
            frame_data: Input frame data
            pixel_format: Target pixel format
            matrix: RGB to Y'CbCr conversion matrix (only used for YUV10)

        Returns:
            Processed frame data ready for output
        """
        if not isinstance(frame_data, np.ndarray):
            raise TypeError("frame_data must be a NumPy array")

        settings = self._current_settings

        if pixel_format == PixelFormat.BGRA:
            if frame_data.dtype != np.uint8:
                frame_data = frame_data.astype(np.uint8)

            if frame_data.ndim == 3 and frame_data.shape[2] == 3:
                # RGB to BGRA conversion
                return _decklink.rgb_to_bgra(frame_data, settings.width, settings.height)
            elif frame_data.ndim == 3 and frame_data.shape[2] == 4:
                # Already BGRA format
                return frame_data
            else:
                raise ValueError("For BGRA format, frame data must be HxWx3 (RGB) or HxWx4 (BGRA)")

        elif pixel_format == PixelFormat.YUV10:
            if frame_data.ndim != 3 or frame_data.shape[2] != 3:
                raise ValueError("For YUV10 format, frame data must be HxWx3 (RGB)")

            # Get the internal Gamut value from the Matrix enum
            internal_matrix = matrix.value

            if frame_data.dtype == np.uint16:
                # RGB uint16 to 10-bit YUV v210 conversion
                return _decklink.rgb_uint16_to_yuv10(frame_data, settings.width, settings.height, internal_matrix)
            elif frame_data.dtype in (np.float32, np.float64):
                # RGB float to 10-bit YUV v210 conversion
                return _decklink.rgb_float_to_yuv10(frame_data.astype(np.float32), settings.width, settings.height, internal_matrix)
            else:
                raise ValueError("For YUV10 format, frame data must be uint16 or float dtype")

        elif pixel_format == PixelFormat.YUV:
            if frame_data.dtype != np.uint8:
                frame_data = frame_data.astype(np.uint8)

            # For YUV format, expect packed YUV422 data
            if frame_data.ndim != 3 or frame_data.shape[2] != 2:
                raise ValueError("For YUV format, frame data must be HxWx2 (packed YUV422)")
            return frame_data

        return frame_data

    def get_display_mode_info(self, display_mode: DisplayMode) -> dict:
        """
        Get information about a display mode.
        
        Args:
            display_mode: Display mode to query
            
        Returns:
            Dictionary with width, height, and framerate information
        """
        settings = self._device.get_video_settings(display_mode.value)
        return {
            'width': settings.width,
            'height': settings.height,
            'framerate': settings.framerate
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()


# Convenience functions
def create_test_pattern(width: int, height: int, pattern: str = 'gradient', grad_start=0.0, grad_end = 1.0) -> np.ndarray:
    """
    Create test patterns for display.

    Args:
        width: Frame width
        height: Frame height
        pattern: Pattern type ('gradient', 'bars', 'checkerboard')
        grad_start: Optional float start value (default 0.0)
        grad_end: Optional float end value (default 1.0)

    Returns:
        RGB frame data as NumPy array (float32, start-end range)
    """
    frame = np.zeros((height, width, 3), dtype=np.float32)

    if pattern == 'gradient':
        for y in range(height):
            for x in range(width):
                frame[y, x] = [
                    grad_start + (grad_end - grad_start) * x / width,      # Red gradient
                    grad_start + (grad_end - grad_start) * x / width,      # Green gradient
                    grad_start + (grad_end - grad_start) * x / width       # Blue gradient
                ]

    elif pattern == 'bars':
        bar_width = width // 8
        colors = [
            [1.0, 1.0, 1.0],      # White
            [1.0, 1.0, 0.0],      # Yellow
            [0.0, 1.0, 1.0],      # Cyan
            [0.0, 1.0, 0.0],      # Green
            [1.0, 0.0, 1.0],      # Magenta
            [1.0, 0.0, 0.0],      # Red
            [0.0, 0.0, 1.0],      # Blue
            [0.0, 0.0, 0.0]       # Black
        ]

        for x in range(width):
            color_idx = min(x // bar_width, 7)
            if color_idx * bar_width == x:
                print(color_idx, colors[color_idx])
            frame[:, x] = colors[color_idx]

    elif pattern == 'checkerboard':
        checker_size = 32
        for y in range(height):
            for x in range(width):
                if ((x // checker_size) + (y // checker_size)) % 2:
                    frame[y, x] = [1.0, 1.0, 1.0]      # White
                else:
                    frame[y, x] = [0.0, 0.0, 0.0]      # Black

    return frame