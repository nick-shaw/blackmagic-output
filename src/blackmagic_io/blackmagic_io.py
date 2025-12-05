"""
Blackmagic DeckLink I/O Library

A Python library for video I/O with Blackmagic DeckLink devices.
Supports video output and input with automatic format conversion.
"""

import numpy as np
from typing import Optional, Tuple, List
from enum import Enum

try:
    import decklink_io as _decklink
except ImportError:
    raise ImportError(
        "DeckLink I/O module not found. Please build and install the C++ extension first. "
        "Run: pip install -e ."
    )


class Matrix(Enum):
    """RGB to Y'CbCr conversion matrix"""
    Rec601 = _decklink.Gamut.Rec601
    Rec709 = _decklink.Gamut.Rec709
    Rec2020 = _decklink.Gamut.Rec2020


class Eotf(Enum):
    """Electro-Optical Transfer Function for HDR"""
    SDR = _decklink.Eotf.SDR
    PQ = _decklink.Eotf.PQ
    HLG = _decklink.Eotf.HLG


class PixelFormat(Enum):
    """Supported pixel formats for DeckLink output"""
    BGRA = _decklink.PixelFormat.BGRA
    YUV8 = _decklink.PixelFormat.YUV8
    YUV10 = _decklink.PixelFormat.YUV10
    RGB10 = _decklink.PixelFormat.RGB10
    RGB12 = _decklink.PixelFormat.RGB12


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
        self._current_input_narrow_range = False
        self._current_output_narrow_range = True

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

    def get_device_capabilities(self, device_index: int = 0) -> dict:
        """
        Get device capabilities (name and supported input/output).

        Args:
            device_index: Index of device to query (default: 0)

        Returns:
            Dictionary with:
            - 'name': Device name
            - 'supports_input': True if device can capture video
            - 'supports_output': True if device can output video
        """
        import decklink_io as _decklink
        caps = _decklink.get_device_capabilities(device_index)
        return {
            'name': caps.name,
            'supports_input': caps.supports_input,
            'supports_output': caps.supports_output
        }

    def is_pixel_format_supported(self, display_mode: DisplayMode,
                                  pixel_format: PixelFormat) -> bool:
        """
        Check if a pixel format is supported for a given display mode.

        Args:
            display_mode: Display mode to check
            pixel_format: Pixel format to check

        Returns:
            True if supported, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Device not initialized. Call initialize() first.")

        return self._device.is_pixel_format_supported(display_mode.value, pixel_format.value)

    def display_static_frame(self, frame_data: np.ndarray,
                           display_mode: DisplayMode,
                           pixel_format: PixelFormat = PixelFormat.YUV10,
                           matrix: Optional[Matrix] = None,
                           hdr_metadata: Optional[dict] = None,
                           input_narrow_range: bool = False,
                           output_narrow_range: bool = True) -> bool:
        """
        Display a static frame continuously.

        Args:
            frame_data: NumPy array containing image data
                       - For RGB: shape should be (height, width, 3)
                       - For BGRA: shape should be (height, width, 4)
                       - Supported dtypes: uint8, uint16, float32, float64
            display_mode: Video resolution and frame rate
            pixel_format: Pixel format (default: YUV10, auto-detected as BGRA for uint8 data)
            matrix: R'G'B' to Y'CbCr conversion matrix (Rec601, Rec709 or Rec2020).
                   Only applies when pixel_format is YUV10.
                   If not specified, auto-detects based on resolution:
                   - SD modes (NTSC, PAL) use Rec.601
                   - HD and higher use Rec.709
            hdr_metadata: Optional HDR metadata dict with keys:
                         - 'eotf': Eotf enum value (SDR, PQ, or HLG)
                         - 'custom': Optional HdrMetadataCustom object
                         If only eotf is provided, default metadata values are used.
            input_narrow_range: For uint16 inputs, whether to interpret values as narrow range.
                              - YUV10: If True, input is narrow (64-940 @10-bit, i.e., 4096-60160 @16-bit).
                                If False (default), input is full range (0-65535).
                              - RGB10/RGB12: If True, input is narrow (64-940 @10-bit, i.e., 4096-60160 @16-bit).
                                If False (default), input is full range (0-65535).
                              - Has no effect for float inputs (always interpreted as full range 0.0-1.0).
                              Default: False
            output_narrow_range: Whether to output narrow range values.
                               - YUV10: If True, Y: 64-940, CbCr: 64-960. If False, full range 0-1023.
                               - RGB10: If True, 64-940. If False, full range 0-1023.
                               - RGB12: If True, 256-3760. If False, full range 0-4095.
                               Default: True

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            if not self.initialize():
                return False

        if pixel_format == PixelFormat.YUV10 and frame_data.dtype == np.uint8:
            pixel_format = PixelFormat.BGRA

        if matrix is None:
            SD_MODES = {DisplayMode.NTSC, DisplayMode.NTSC2398, DisplayMode.PAL,
                       DisplayMode.NTSCp, DisplayMode.PALp}
            if display_mode in SD_MODES:
                matrix = Matrix.Rec601
            else:
                matrix = Matrix.Rec709

        self._current_matrix = matrix
        self._current_input_narrow_range = input_narrow_range
        self._current_output_narrow_range = output_narrow_range

        gamut = matrix.value

        if hdr_metadata is not None:
            eotf = hdr_metadata.get('eotf')
            if eotf is None:
                raise ValueError("hdr_metadata must contain 'eotf' key")

            custom = hdr_metadata.get('custom')

            if custom is not None:
                self._device.set_hdr_metadata_custom(gamut, eotf.value, custom)
            else:
                self._device.set_hdr_metadata(gamut, eotf.value)
        else:
            self._device.clear_hdr_metadata()
            self._device.set_hdr_metadata(gamut, Eotf.SDR.value)

        if (not self._current_settings or
            self._current_settings.mode != display_mode.value or
            self._current_settings.format != pixel_format.value or
            not self._output_started):
            settings = self._device.get_video_settings(display_mode.value)
            settings.format = pixel_format.value

            if not self._device.setup_output(settings):
                return False
            self._current_settings = settings

        processed_frame = self._prepare_frame_data(frame_data, pixel_format, matrix, input_narrow_range, output_narrow_range)

        if not self._device.set_frame_data(processed_frame):
            return False

        if self._device.display_frame():
            self._output_started = True
            return True

        return False

    def display_solid_color(self, color: Tuple,
                          display_mode: DisplayMode,
                          pixel_format: PixelFormat = PixelFormat.YUV10,
                          matrix: Optional[Matrix] = None,
                          hdr_metadata: Optional[dict] = None,
                          input_narrow_range: bool = False,
                          output_narrow_range: bool = True,
                          patch: Optional[Tuple[float, float, float, float]] = None,
                          background_color: Optional[Tuple] = None) -> bool:
        """
        Display a solid color frame continuously.

        Args:
            color: R'G'B' tuple (r, g, b) with values:
                   - Integer values (0-1023): Interpreted as 10-bit values
                   - Float values (0.0-1.0): Interpreted as normalized full range values
            display_mode: Video resolution and frame rate
            pixel_format: Pixel format (default: YUV10)
            matrix: R'G'B' to Y'CbCr conversion matrix (Rec601, Rec709 or Rec2020).
                   Only applies when pixel_format is YUV10.
                   If not specified, auto-detects based on resolution:
                   - SD modes (NTSC, PAL) use Rec.601
                   - HD and higher use Rec.709
            hdr_metadata: Optional HDR metadata dict with keys:
                         - 'eotf': Eotf enum value (SDR, PQ, or HLG)
                         - 'custom': Optional HdrMetadataCustom object
                         If only eotf is provided, default metadata values are used.
            input_narrow_range: For integer inputs, whether to interpret values as narrow range.
                              If True, values are narrow (64-940). If False (default), full range (0-1023).
                              Has no effect for float inputs (always full range 0.0-1.0).
                              Default: False
            output_narrow_range: Whether to output narrow range values.
                               - YUV10: If True, Y: 64-940, CbCr: 64-960. If False, full range 0-1023.
                               - RGB10: If True, 64-940. If False, full range 0-1023.
                               - RGB12: If True, 256-3760. If False, full range 0-4095.
                               Default: True
            patch: Optional tuple (center_x, center_y, width, height) with normalized coordinates (0.0-1.0).
                  - center_x, center_y: Center position of the patch (0.5, 0.5 = center of screen)
                  - width, height: Patch dimensions (1.0, 1.0 = full screen)
                  If None, displays full screen solid color. Default: None
            background_color: R'G'B' tuple for background when using patch parameter.
                            Uses same format as color parameter (integer 0-1023 or float 0.0-1.0).
                            If None, defaults to black. Default: None

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            if not self.initialize():
                return False

        settings = self._device.get_video_settings(display_mode.value)

        is_float = isinstance(color[0], float)

        if patch is None:
            if is_float:
                frame_data = np.full((settings.height, settings.width, 3),
                                   color, dtype=np.float32)
            else:
                color_uint16 = tuple(int(c) << 6 for c in color)
                frame_data = np.full((settings.height, settings.width, 3),
                                   color_uint16, dtype=np.uint16)
        else:
            center_x, center_y, patch_width, patch_height = patch

            if background_color is None:
                if is_float:
                    background_color = (0.0, 0.0, 0.0)
                else:
                    black_value = 64 if input_narrow_range else 0
                    background_color = (black_value, black_value, black_value)

            if is_float:
                frame_data = np.full((settings.height, settings.width, 3),
                                   background_color, dtype=np.float32)
                patch_color = color
            else:
                bg_uint16 = tuple(int(c) << 6 for c in background_color)
                frame_data = np.full((settings.height, settings.width, 3),
                                   bg_uint16, dtype=np.uint16)
                patch_color = tuple(int(c) << 6 for c in color)

            patch_pixel_width = int(patch_width * settings.width)
            patch_pixel_height = int(patch_height * settings.height)
            center_pixel_x = int(center_x * settings.width)
            center_pixel_y = int(center_y * settings.height)

            left = max(0, center_pixel_x - patch_pixel_width // 2)
            right = min(settings.width, center_pixel_x + (patch_pixel_width + 1) // 2)
            top = max(0, center_pixel_y - patch_pixel_height // 2)
            bottom = min(settings.height, center_pixel_y + (patch_pixel_height + 1) // 2)

            frame_data[top:bottom, left:right] = patch_color

        return self.display_static_frame(frame_data, display_mode, pixel_format, matrix, hdr_metadata,
                                       input_narrow_range, output_narrow_range)

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

        if self._current_settings.format == _decklink.PixelFormat.BGRA:
            pixel_format = PixelFormat.BGRA
        elif self._current_settings.format == _decklink.PixelFormat.YUV8:
            pixel_format = PixelFormat.YUV8
        elif self._current_settings.format == _decklink.PixelFormat.YUV10:
            pixel_format = PixelFormat.YUV10
        elif self._current_settings.format == _decklink.PixelFormat.RGB10:
            pixel_format = PixelFormat.RGB10
        elif self._current_settings.format == _decklink.PixelFormat.RGB12:
            pixel_format = PixelFormat.RGB12
        else:
            raise RuntimeError(f"Unsupported pixel format in current settings: {self._current_settings.format}")

        processed_frame = self._prepare_frame_data(frame_data, pixel_format, self._current_matrix,
                                                  self._current_input_narrow_range, self._current_output_narrow_range)

        if not self._device.set_frame_data(processed_frame):
            return False

        return self._device.display_frame()

    def stop(self) -> bool:
        """
        Stop video output.

        Returns:
            True if successful, False otherwise
        """
        if self._output_started:
            result = self._device.stop_output()
            self._output_started = False
            return result
        return True

    def cleanup(self):
        """
        Cleanup resources and stop output.
        """
        self.stop()
        self._device.cleanup()
        self._initialized = False

    def _prepare_frame_data(self, frame_data: np.ndarray,
                          pixel_format: PixelFormat,
                          matrix: Matrix = Matrix.Rec709,
                          input_narrow_range: bool = False,
                          output_narrow_range: bool = True) -> np.ndarray:
        """
        Prepare frame data for output, converting format if necessary.

        Args:
            frame_data: Input frame data
            pixel_format: Target pixel format
            matrix: RGB to Y'CbCr conversion matrix (only used for YUV10)
            input_narrow_range: For uint16 inputs, whether to interpret as narrow range
            output_narrow_range: Whether to output narrow range values

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
                return _decklink.rgb_to_bgra(frame_data, settings.width, settings.height)
            elif frame_data.ndim == 3 and frame_data.shape[2] == 4:
                return frame_data
            else:
                raise ValueError("For BGRA format, frame data must be HxWx3 (RGB) or HxWx4 (BGRA)")

        elif pixel_format == PixelFormat.YUV8:
            if frame_data.ndim != 3 or frame_data.shape[2] != 3:
                raise ValueError("For YUV8 format, frame data must be HxWx3 (RGB)")

            internal_matrix = matrix.value

            if frame_data.dtype == np.uint8:
                return _decklink.rgb_uint8_to_yuv8(frame_data, settings.width, settings.height,
                                                   internal_matrix, input_narrow_range, output_narrow_range)
            elif frame_data.dtype == np.uint16:
                return _decklink.rgb_uint16_to_yuv8(frame_data, settings.width, settings.height,
                                                    internal_matrix, input_narrow_range, output_narrow_range)
            elif frame_data.dtype in (np.float32, np.float64):
                return _decklink.rgb_float_to_yuv8(frame_data.astype(np.float32), settings.width, settings.height,
                                                   internal_matrix, output_narrow_range)
            else:
                raise ValueError("For YUV8 format, frame data must be uint8, uint16 or float dtype")

        elif pixel_format == PixelFormat.YUV10:
            if frame_data.ndim != 3 or frame_data.shape[2] != 3:
                raise ValueError("For YUV10 format, frame data must be HxWx3 (RGB)")

            internal_matrix = matrix.value

            if frame_data.dtype == np.uint16:
                return _decklink.rgb_uint16_to_yuv10(frame_data, settings.width, settings.height,
                                                     internal_matrix, input_narrow_range, output_narrow_range)
            elif frame_data.dtype in (np.float32, np.float64):
                return _decklink.rgb_float_to_yuv10(frame_data.astype(np.float32), settings.width, settings.height,
                                                    internal_matrix, output_narrow_range)
            else:
                raise ValueError("For YUV10 format, frame data must be uint16 or float dtype")

        elif pixel_format == PixelFormat.RGB10:
            if frame_data.ndim != 3 or frame_data.shape[2] != 3:
                raise ValueError("For RGB10 format, frame data must be HxWx3 (RGB)")

            if frame_data.dtype == np.uint16:
                return _decklink.rgb_uint16_to_rgb10(frame_data, settings.width, settings.height,
                                                     input_narrow_range, output_narrow_range)
            elif frame_data.dtype in (np.float32, np.float64):
                return _decklink.rgb_float_to_rgb10(frame_data.astype(np.float32), settings.width, settings.height,
                                                    output_narrow_range)
            else:
                raise ValueError("For RGB10 format, frame data must be uint16 or float dtype")

        elif pixel_format == PixelFormat.RGB12:
            if frame_data.ndim != 3 or frame_data.shape[2] != 3:
                raise ValueError("For RGB12 format, frame data must be HxWx3 (RGB)")

            if frame_data.dtype == np.uint16:
                return _decklink.rgb_uint16_to_rgb12(frame_data, settings.width, settings.height,
                                                     input_narrow_range, output_narrow_range)
            elif frame_data.dtype in (np.float32, np.float64):
                return _decklink.rgb_float_to_rgb12(frame_data.astype(np.float32), settings.width, settings.height,
                                                    output_narrow_range)
            else:
                raise ValueError("For RGB12 format, frame data must be uint16 or float dtype")

        else:
            raise ValueError(f"Unsupported pixel format: {pixel_format}")

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

    def get_current_output_info(self) -> dict:
        """
        Get information about the current output configuration.

        Returns:
            Dictionary with current output settings including:
            - display_mode_name: Human-readable display mode name
            - pixel_format_name: Human-readable pixel format name
            - width: Frame width
            - height: Frame height
            - framerate: Frame rate
            - rgb444_mode_enabled: Whether RGB 4:4:4 mode is enabled
        """
        info = self._device.get_current_output_info()
        return {
            'display_mode_name': info.display_mode_name,
            'pixel_format_name': info.pixel_format_name,
            'width': info.width,
            'height': info.height,
            'framerate': info.framerate,
            'rgb444_mode_enabled': info.rgb444_mode_enabled
        }

    def get_supported_display_modes(self) -> List[dict]:
        """
        Get list of supported display modes for the initialized device.

        Returns:
            List of dictionaries, each containing:
            - display_mode: DisplayMode enum value
            - name: Human-readable mode name
            - width: Frame width
            - height: Frame height
            - framerate: Frame rate

        Raises:
            RuntimeError: If device not initialized
        """
        if not self._initialized:
            raise RuntimeError("Device not initialized. Call initialize() first.")

        modes = self._device.get_supported_display_modes()
        return [
            {
                'display_mode': DisplayMode(mode.display_mode),
                'name': mode.name,
                'width': mode.width,
                'height': mode.height,
                'framerate': mode.framerate
            }
            for mode in modes
        ]

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
        for x in range(width):
            frame[:, x, :] = [grad_start + (grad_end - grad_start) * x / (width - 1)]

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


class BlackmagicInput:
    """
    High-level interface for capturing video from Blackmagic DeckLink devices.

    This class provides simplified video capture with automatic format detection
    and conversion to RGB float arrays.

    Usage:
        with BlackmagicInput() as input:
            input.initialize()
            rgb_frame = input.capture_frame_as_rgb()
    """

    def __init__(self):
        """Initialize the BlackmagicInput interface."""
        self._input = _decklink.DeckLinkInput()
        self._initialized = False
        self._capturing = False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
        return False

    def initialize(self, device_index: int = 0, input_connection=None, pixel_format: Optional[PixelFormat] = None) -> bool:
        """Initialize DeckLink device for input and start capture.

        Immediately activates capture mode, which will:
        - Start accepting input signal
        - Activate front panel display (if present)
        - Enable format detection

        Args:
            device_index: Index of device to use (default: 0)
            input_connection: Optional InputConnection enum to select specific input
                (e.g., InputConnection.SDI, InputConnection.HDMI). If None, uses
                the device's current/default input.
            pixel_format: Optional PixelFormat to request from hardware.
                Use PixelFormat.BGRA for fast preview. If None, defaults to YUV10.

        Returns:
            True if successful, False otherwise
        """
        if self._input.initialize(device_index, input_connection):
            self._initialized = True
            if pixel_format is None:
                capture_result = self._input.start_capture()
            else:
                capture_result = self._input.start_capture(pixel_format.value)
            if capture_result:
                self._capturing = True
                return True
            return False
        return False

    def get_available_devices(self) -> List[str]:
        """Get list of available DeckLink devices.

        Returns:
            List of device names
        """
        return self._input.get_device_list()

    def get_device_capabilities(self, device_index: int = 0) -> dict:
        """
        Get device capabilities (name and supported input/output).

        Args:
            device_index: Index of device to query (default: 0)

        Returns:
            Dictionary with:
            - 'name': Device name
            - 'supports_input': True if device can capture video
            - 'supports_output': True if device can output video
        """
        import decklink_io as _decklink
        caps = _decklink.get_device_capabilities(device_index)
        return {
            'name': caps.name,
            'supports_input': caps.supports_input,
            'supports_output': caps.supports_output
        }

    def get_available_input_connections(self, device_index: int = 0) -> List:
        """Get available input connections for a DeckLink device.

        Args:
            device_index: Index of device to query (default: 0)

        Returns:
            List of InputConnection enum values (e.g., [InputConnection.SDI, InputConnection.HDMI])
        """
        return self._input.get_available_input_connections(device_index)

    def capture_frame_as_uint8(self,
                              timeout_ms: int = 5000,
                              input_narrow_range: bool = True) -> Optional[np.ndarray]:
        """Capture a frame and convert to RGB uint8 array (faster than float).

        Automatically detects pixel format and converts to RGB uint8 (0-255).
        Uses colorspace metadata from the captured frame for YUV conversion.

        Args:
            timeout_ms: Capture timeout in milliseconds (default: 5000)
            input_narrow_range: Whether input uses narrow range encoding (default: True)

        Returns:
            RGB array (H×W×3), dtype uint8, range 0-255, or None if capture failed
        """
        if not self._capturing:
            if not self._input.start_capture():
                return None
            self._capturing = True

        captured_frame = _decklink.CapturedFrame()
        if not self._input.capture_frame(captured_frame, timeout_ms):
            return None

        return self._convert_frame_to_uint8(captured_frame, input_narrow_range)

    def capture_frame_as_uint8_with_metadata(self,
                                            timeout_ms: int = 5000,
                                            input_narrow_range: bool = True) -> Optional[dict]:
        """Capture a frame and convert to RGB uint8 with metadata (fast preview with metadata).

        Automatically detects pixel format and converts to RGB uint8 (0-255).
        Uses colorspace metadata from the captured frame for YUV conversion.

        Args:
            timeout_ms: Capture timeout in milliseconds (default: 5000)
            input_narrow_range: Whether input uses narrow range encoding (default: True)

        Returns:
            Dictionary with:
                - 'rgb': RGB array (H×W×3), dtype uint8, range 0-255
                - 'width': int
                - 'height': int
                - 'format': PixelFormat name
                - 'mode': DisplayMode name
                - 'colorspace': Matrix name (Rec.601/709/2020)
                - 'eotf': Eotf name (SDR/PQ/HLG)
                - 'input_narrow_range': bool (what was used for conversion)
                - 'hdr_metadata': dict with HDR metadata (if present):
                    - 'display_primaries': dict with 'red', 'green', 'blue' (each with 'x', 'y')
                    - 'white_point': dict with 'x', 'y'
                    - 'mastering_luminance': dict with 'max', 'min' (cd/m²)
                    - 'content_light': dict with 'max_cll', 'max_fall' (cd/m²)
            Or None if capture failed
        """
        if not self._capturing:
            if not self._input.start_capture():
                return None
            self._capturing = True

        captured_frame = _decklink.CapturedFrame()
        if not self._input.capture_frame(captured_frame, timeout_ms):
            return None

        rgb_array = self._convert_frame_to_uint8(captured_frame, input_narrow_range)
        if rgb_array is None:
            return None

        pixel_format = PixelFormat(captured_frame.format)
        colorspace = Matrix(captured_frame.colorspace)
        eotf = Eotf(captured_frame.eotf)

        display_mode = None
        for mode in DisplayMode:
            if mode.value == captured_frame.mode:
                display_mode = mode
                break

        result = {
            'rgb': rgb_array,
            'width': captured_frame.width,
            'height': captured_frame.height,
            'format': pixel_format.name,
            'mode': display_mode.name if display_mode else 'Unknown',
            'colorspace': colorspace.name,
            'eotf': eotf.name,
            'input_narrow_range': input_narrow_range
        }

        hdr_metadata = {}

        if captured_frame.has_display_primaries:
            hdr_metadata['display_primaries'] = {
                'red': {
                    'x': captured_frame.display_primaries_red_x,
                    'y': captured_frame.display_primaries_red_y
                },
                'green': {
                    'x': captured_frame.display_primaries_green_x,
                    'y': captured_frame.display_primaries_green_y
                },
                'blue': {
                    'x': captured_frame.display_primaries_blue_x,
                    'y': captured_frame.display_primaries_blue_y
                }
            }

        if captured_frame.has_white_point:
            hdr_metadata['white_point'] = {
                'x': captured_frame.white_point_x,
                'y': captured_frame.white_point_y
            }

        if captured_frame.has_mastering_luminance:
            hdr_metadata['mastering_luminance'] = {
                'max': captured_frame.max_display_mastering_luminance,
                'min': captured_frame.min_display_mastering_luminance
            }

        content_light = {}
        if captured_frame.has_max_cll:
            content_light['max_cll'] = captured_frame.max_content_light_level
        if captured_frame.has_max_fall:
            content_light['max_fall'] = captured_frame.max_frame_average_light_level
        if content_light:
            hdr_metadata['content_light'] = content_light

        if hdr_metadata:
            result['hdr_metadata'] = hdr_metadata

        return result

    def capture_frame_as_rgb(self,
                            timeout_ms: int = 5000,
                            input_narrow_range: bool = True) -> Optional[np.ndarray]:
        """Capture a frame and convert to RGB float array.

        Automatically detects pixel format and converts to RGB float (0.0-1.0).
        Uses colorspace metadata from the captured frame for YUV conversion.

        Args:
            timeout_ms: Capture timeout in milliseconds (default: 5000)
            input_narrow_range: Whether input uses narrow range encoding (default: True)
                - YUV8: True = 16-235/16-240 (standard)
                - YUV10: True = 64-940/64-960 (standard)
                - RGB10: True = 64-940 (convention)
                - RGB12: False = 0-4095 (convention) - override to False for RGB12 full range

        Returns:
            RGB array (H×W×3), dtype float32, range 0.0-1.0, or None if capture failed
        """
        if not self._capturing:
            if not self._input.start_capture():
                return None
            self._capturing = True

        captured_frame = _decklink.CapturedFrame()
        if not self._input.capture_frame(captured_frame, timeout_ms):
            return None

        return self._convert_frame_to_rgb(captured_frame, input_narrow_range)

    def capture_frame_with_metadata(self,
                                   timeout_ms: int = 5000,
                                   input_narrow_range: bool = True) -> Optional[dict]:
        """Capture a frame with full metadata.

        Args:
            timeout_ms: Capture timeout in milliseconds (default: 5000)
            input_narrow_range: Whether input uses narrow range encoding (default: True)

        Returns:
            Dictionary with:
                - 'rgb': RGB array (H×W×3), dtype float32, range 0.0-1.0
                - 'width': int
                - 'height': int
                - 'format': PixelFormat
                - 'mode': DisplayMode
                - 'colorspace': Matrix (Rec.601/709/2020)
                - 'eotf': Eotf (SDR/PQ/HLG)
                - 'input_narrow_range': bool (what was used for conversion)
                - 'hdr_metadata': dict with HDR metadata (if present):
                    - 'display_primaries': dict with 'red', 'green', 'blue' (each with 'x', 'y')
                    - 'white_point': dict with 'x', 'y'
                    - 'mastering_luminance': dict with 'max', 'min' (cd/m²)
                    - 'content_light': dict with 'max_cll', 'max_fall' (cd/m²)
            Or None if capture failed
        """
        if not self._capturing:
            if not self._input.start_capture():
                return None
            self._capturing = True

        captured_frame = _decklink.CapturedFrame()
        if not self._input.capture_frame(captured_frame, timeout_ms):
            return None

        rgb_array = self._convert_frame_to_rgb(captured_frame, input_narrow_range)
        if rgb_array is None:
            return None

        pixel_format = PixelFormat(captured_frame.format)
        colorspace = Matrix(captured_frame.colorspace)
        eotf = Eotf(captured_frame.eotf)

        display_mode = None
        for mode in DisplayMode:
            if mode.value == captured_frame.mode:
                display_mode = mode
                break

        result = {
            'rgb': rgb_array,
            'width': captured_frame.width,
            'height': captured_frame.height,
            'format': pixel_format.name,
            'mode': display_mode.name if display_mode else 'Unknown',
            'colorspace': colorspace.name,
            'eotf': eotf.name,
            'input_narrow_range': input_narrow_range
        }

        hdr_metadata = {}

        if captured_frame.has_display_primaries:
            hdr_metadata['display_primaries'] = {
                'red': {
                    'x': captured_frame.display_primaries_red_x,
                    'y': captured_frame.display_primaries_red_y
                },
                'green': {
                    'x': captured_frame.display_primaries_green_x,
                    'y': captured_frame.display_primaries_green_y
                },
                'blue': {
                    'x': captured_frame.display_primaries_blue_x,
                    'y': captured_frame.display_primaries_blue_y
                }
            }

        if captured_frame.has_white_point:
            hdr_metadata['white_point'] = {
                'x': captured_frame.white_point_x,
                'y': captured_frame.white_point_y
            }

        if captured_frame.has_mastering_luminance:
            hdr_metadata['mastering_luminance'] = {
                'max': captured_frame.max_display_mastering_luminance,
                'min': captured_frame.min_display_mastering_luminance
            }

        content_light = {}
        if captured_frame.has_max_cll:
            content_light['max_cll'] = captured_frame.max_content_light_level
        if captured_frame.has_max_fall:
            content_light['max_fall'] = captured_frame.max_frame_average_light_level
        if content_light:
            hdr_metadata['content_light'] = content_light

        if hdr_metadata:
            result['hdr_metadata'] = hdr_metadata

        return result

    def get_detected_format(self) -> Optional[dict]:
        """Get detected format information.

        Must be called after start_capture() has detected a signal.

        Returns:
            Dictionary with 'mode', 'width', 'height', 'framerate', or None if not available
        """
        if not self._capturing:
            return None

        try:
            detected = self._input.get_detected_format()
            mode = DisplayMode(detected.mode)
            return {
                'mode': mode.name,
                'width': detected.width,
                'height': detected.height,
                'framerate': detected.framerate
            }
        except:
            return None

    def stop_capture(self) -> bool:
        """Stop video capture.

        Returns:
            True if successful
        """
        if self._capturing:
            result = self._input.stop_capture()
            self._capturing = False
            return result
        return True

    def cleanup(self):
        """Cleanup and release all resources.

        Stops capture if running and releases the device.
        """
        if self._capturing:
            self.stop_capture()
        if self._initialized:
            self._input.cleanup()
            self._initialized = False

    def _convert_frame_to_uint8(self, captured_frame, input_narrow_range: bool) -> Optional[np.ndarray]:
        """Convert captured frame to RGB uint8 array.

        Args:
            captured_frame: CapturedFrame object from low-level API
            input_narrow_range: Whether to interpret input as narrow range

        Returns:
            RGB array (H×W×3), dtype uint8, or None if conversion failed
        """
        frame_data = np.array(captured_frame.data, dtype=np.uint8)
        width = captured_frame.width
        height = captured_frame.height
        pixel_format = captured_frame.format

        try:
            if pixel_format == _decklink.PixelFormat.YUV8:
                rgb_uint16 = _decklink.yuv8_to_rgb_uint16(
                    frame_data, width, height,
                    matrix=captured_frame.colorspace,
                    input_narrow_range=input_narrow_range,
                    output_narrow_range=False
                )
                return (rgb_uint16 >> 8).astype(np.uint8)

            elif pixel_format == _decklink.PixelFormat.YUV10:
                rgb_uint16 = _decklink.yuv10_to_rgb_uint16(
                    frame_data, width, height,
                    matrix=captured_frame.colorspace,
                    input_narrow_range=input_narrow_range,
                    output_narrow_range=False
                )
                return (rgb_uint16 >> 8).astype(np.uint8)

            elif pixel_format == _decklink.PixelFormat.RGB10:
                rgb_uint16 = _decklink.rgb10_to_uint16(
                    frame_data, width, height,
                    input_narrow_range=input_narrow_range,
                    output_narrow_range=False
                )
                return (rgb_uint16 >> 8).astype(np.uint8)

            elif pixel_format == _decklink.PixelFormat.RGB12:
                rgb_uint16 = _decklink.rgb12_to_uint16(
                    frame_data, width, height,
                    input_narrow_range=input_narrow_range,
                    output_narrow_range=False
                )
                return (rgb_uint16 >> 8).astype(np.uint8)

            elif pixel_format == _decklink.PixelFormat.BGRA:
                bgra_data = np.frombuffer(frame_data, dtype=np.uint8).reshape(
                    (height, width, 4)
                )
                rgb_array = np.empty((height, width, 3), dtype=np.uint8)
                rgb_array[:, :, 0] = bgra_data[:, :, 2]  # R
                rgb_array[:, :, 1] = bgra_data[:, :, 1]  # G
                rgb_array[:, :, 2] = bgra_data[:, :, 0]  # B
                return rgb_array

            else:
                return None

        except Exception:
            return None

    def _convert_frame_to_rgb(self, captured_frame, input_narrow_range: bool) -> Optional[np.ndarray]:
        """Convert captured frame to RGB float array.

        Args:
            captured_frame: CapturedFrame object from low-level API
            input_narrow_range: Whether to interpret input as narrow range

        Returns:
            RGB array (H×W×3), dtype float32, or None if conversion failed
        """
        frame_data = np.array(captured_frame.data, dtype=np.uint8)
        width = captured_frame.width
        height = captured_frame.height
        pixel_format = captured_frame.format

        try:
            if pixel_format == _decklink.PixelFormat.YUV8:
                return _decklink.yuv8_to_rgb_float(
                    frame_data, width, height,
                    matrix=captured_frame.colorspace,
                    input_narrow_range=input_narrow_range
                )

            elif pixel_format == _decklink.PixelFormat.YUV10:
                return _decklink.yuv10_to_rgb_float(
                    frame_data, width, height,
                    matrix=captured_frame.colorspace,
                    input_narrow_range=input_narrow_range
                )

            elif pixel_format == _decklink.PixelFormat.RGB10:
                return _decklink.rgb10_to_float(
                    frame_data, width, height,
                    input_narrow_range=input_narrow_range
                )

            elif pixel_format == _decklink.PixelFormat.RGB12:
                return _decklink.rgb12_to_float(
                    frame_data, width, height,
                    input_narrow_range=input_narrow_range
                )

            elif pixel_format == _decklink.PixelFormat.BGRA:
                bgra_data = np.frombuffer(frame_data, dtype=np.uint8).reshape(
                    (height, width, 4)
                )
                rgb_array = np.zeros((height, width, 3), dtype=np.float32)
                rgb_array[:, :, 0] = bgra_data[:, :, 2] / 255.0  # R
                rgb_array[:, :, 1] = bgra_data[:, :, 1] / 255.0  # G
                rgb_array[:, :, 2] = bgra_data[:, :, 0] / 255.0  # B
                return rgb_array

            else:
                return None

        except Exception:
            return None