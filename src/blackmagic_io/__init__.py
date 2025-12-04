"""
Blackmagic DeckLink I/O Library

A Python library for video I/O with Blackmagic DeckLink devices.
Supports video output and input, with automatic format conversion.
"""

import numpy as np

from .blackmagic_io import (
    BlackmagicOutput,
    BlackmagicInput,
    DisplayMode,
    PixelFormat,
    Matrix,
    Eotf,
    create_test_pattern,
)

# Import InputConnection from low-level API
try:
    from decklink_io import InputConnection
except ImportError:
    InputConnection = None

# Re-export low-level API for advanced use
try:
    import decklink_io
    from decklink_io import (
        DeckLinkOutput,
        DeckLinkInput,
        VideoSettings,
        HdrMetadataCustom,
        DisplayModeInfo,
        CapturedFrame,
        DeviceCapabilities,
        Gamut,
        Eotf as _Eotf,
        Matrix as _Matrix,
        get_device_capabilities,
    )
    # Import C++ conversion functions with underscore prefix
    from decklink_io import (
        # Packing (RGB -> format)
        rgb_to_bgra as _rgb_to_bgra,
        rgb_uint8_to_yuv8 as _rgb_uint8_to_yuv8,
        rgb_uint16_to_yuv8 as _rgb_uint16_to_yuv8,
        rgb_float_to_yuv8 as _rgb_float_to_yuv8,
        rgb_uint16_to_yuv10 as _rgb_uint16_to_yuv10,
        rgb_float_to_yuv10 as _rgb_float_to_yuv10,
        rgb_uint16_to_rgb10 as _rgb_uint16_to_rgb10,
        rgb_float_to_rgb10 as _rgb_float_to_rgb10,
        rgb_uint16_to_rgb12 as _rgb_uint16_to_rgb12,
        rgb_float_to_rgb12 as _rgb_float_to_rgb12,
        # Unpacking (format -> RGB)
        yuv10_to_rgb_uint16 as _yuv10_to_rgb_uint16,
        yuv10_to_rgb_float as _yuv10_to_rgb_float,
        yuv8_to_rgb_uint16 as _yuv8_to_rgb_uint16,
        yuv8_to_rgb_float as _yuv8_to_rgb_float,
        rgb10_to_uint16 as _rgb10_to_uint16,
        rgb10_to_float as _rgb10_to_float,
        rgb12_to_uint16 as _rgb12_to_uint16,
        rgb12_to_float as _rgb12_to_float,
        # Unpacking (format -> components)
        unpack_v210 as _unpack_v210,
        unpack_2vuy as _unpack_2vuy,
        unpack_rgb10 as _unpack_rgb10,
        unpack_rgb12 as _unpack_rgb12,
    )

    # Wrap conversion functions to ensure C-contiguous arrays
    def rgb_to_bgra(rgb_array, width, height):
        """Convert RGB numpy array to BGRA format.

        Automatically converts input array to C-contiguous layout if needed.

        Args:
            rgb_array: HxWx3 RGB array (uint8)
            width: Image width
            height: Image height

        Returns:
            HxWx4 BGRA array (uint8)
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_to_bgra(rgb_array, width, height)

    def rgb_uint8_to_yuv8(rgb_array, width, height, matrix=Gamut.Rec709,
                          input_narrow_range=False, output_narrow_range=True):
        """Convert RGB uint8 numpy array to 8-bit YUV 2vuy format.

        Automatically converts input array to C-contiguous layout if needed.

        Args:
            rgb_array: HxWx3 RGB array (uint8)
            width: Image width
            height: Image height
            matrix: Color matrix (Rec601, Rec709, or Rec2020)
            input_narrow_range: If True, input is narrow range (16-235); if False, full range (0-255)
            output_narrow_range: If True, output is narrow range (Y: 16-235, CbCr: 16-240); if False, full range

        Returns:
            Flat uint8 array in 2vuy format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_uint8_to_yuv8(rgb_array, width, height, matrix, input_narrow_range, output_narrow_range)

    def rgb_uint16_to_yuv8(rgb_array, width, height, matrix=Gamut.Rec709, input_narrow_range=False, output_narrow_range=True):
        """Convert RGB uint16 numpy array to 8-bit YUV 2vuy format.

        Automatically converts input array to C-contiguous layout if needed.

        Args:
            rgb_array: HxWx3 RGB array (uint16)
            width: Image width
            height: Image height
            matrix: Color matrix (Rec601, Rec709, or Rec2020)
            input_narrow_range: If True, input is narrow range (64-940 @10-bit, i.e., 4096-60160 @16-bit).
                              If False, input is full range (0-65535). Default: False
            output_narrow_range: If True, output YUV is narrow range (Y: 16-235, CbCr: 16-240).
                               If False, output is full range (0-255). Default: True

        Returns:
            Flat uint8 array in 2vuy format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_uint16_to_yuv8(rgb_array, width, height, matrix, input_narrow_range, output_narrow_range)

    def rgb_float_to_yuv8(rgb_array, width, height, matrix=Gamut.Rec709, output_narrow_range=True):
        """Convert RGB float numpy array to 8-bit YUV 2vuy format.

        Automatically converts input array to C-contiguous layout if needed.

        Note: Float input is always interpreted as full range (0.0-1.0).

        Args:
            rgb_array: HxWx3 RGB array (float, 0.0-1.0 full range)
            width: Image width
            height: Image height
            matrix: Color matrix (Rec601, Rec709, or Rec2020)
            output_narrow_range: If True, output YUV is narrow range (Y: 16-235, CbCr: 16-240).
                               If False, output is full range (0-255). Default: True

        Returns:
            Flat uint8 array in 2vuy format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_float_to_yuv8(rgb_array, width, height, matrix, output_narrow_range)

    def rgb_uint16_to_yuv10(rgb_array, width, height, matrix=Gamut.Rec709, input_narrow_range=False, output_narrow_range=True):
        """Convert RGB uint16 numpy array to 10-bit YUV v210 format.

        Automatically converts input array to C-contiguous layout if needed.

        Args:
            rgb_array: HxWx3 RGB array (uint16)
            width: Image width
            height: Image height
            matrix: Color matrix (Rec601, Rec709, or Rec2020)
            input_narrow_range: If True, input is narrow range (64-940 @10-bit, i.e., 4096-60160 @16-bit).
                              If False, input is full range (0-65535). Default: False
            output_narrow_range: If True, output YUV is narrow range (Y: 64-940, CbCr: 64-960).
                               If False, output is full range (0-1023). Default: True

        Returns:
            Flat uint8 array in v210 format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_uint16_to_yuv10(rgb_array, width, height, matrix, input_narrow_range, output_narrow_range)

    def rgb_float_to_yuv10(rgb_array, width, height, matrix=Gamut.Rec709, output_narrow_range=True):
        """Convert RGB float numpy array to 10-bit YUV v210 format.

        Automatically converts input array to C-contiguous layout if needed.

        Note: Float input is always interpreted as full range (0.0-1.0). If you have narrow range
        float values, convert to full range first. The conversion depends on source bit depth.
        Example for 10-bit source: rgb_full = (rgb_narrow - 64/1023) / (876/1023)

        Args:
            rgb_array: HxWx3 RGB array (float, 0.0-1.0 full range)
            width: Image width
            height: Image height
            matrix: Color matrix (Rec601, Rec709, or Rec2020)
            output_narrow_range: If True, output YUV is narrow range (Y: 64-940, CbCr: 64-960).
                               If False, output is full range (0-1023). Default: True

        Returns:
            Flat uint8 array in v210 format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_float_to_yuv10(rgb_array, width, height, matrix, output_narrow_range)

    def rgb_uint16_to_rgb10(rgb_array, width, height, input_narrow_range=True, output_narrow_range=True):
        """Convert RGB uint16 numpy array to 10-bit RGB r210 format.

        Automatically converts input array to C-contiguous layout if needed.

        Args:
            rgb_array: HxWx3 RGB array (uint16)
            width: Image width
            height: Image height
            input_narrow_range: If True, input is narrow range (64-940 @10-bit, i.e., 4096-60160 @16-bit).
                              If False, input is full range (0-65535). Default: True
            output_narrow_range: If True, output is narrow range (64-940).
                               If False, output is full range (0-1023). Default: True

        Returns:
            Flat uint8 array in r210 format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_uint16_to_rgb10(rgb_array, width, height, input_narrow_range, output_narrow_range)

    def rgb_float_to_rgb10(rgb_array, width, height, output_narrow_range=True):
        """Convert RGB float numpy array to 10-bit RGB r210 format.

        Automatically converts input array to C-contiguous layout if needed.

        Args:
            rgb_array: HxWx3 RGB array (float, 0.0-1.0 full range)
            width: Image width
            height: Image height
            output_narrow_range: If True, map 0.0-1.0 to 64-940 (narrow range).
                               If False, map 0.0-1.0 to 0-1023 (full range). Default: True

        Returns:
            Flat uint8 array in r210 format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_float_to_rgb10(rgb_array, width, height, output_narrow_range)

    def rgb_uint16_to_rgb12(rgb_array, width, height, input_narrow_range=False, output_narrow_range=False):
        """Convert RGB uint16 numpy array to 12-bit RGB format.

        Automatically converts input array to C-contiguous layout if needed.

        Args:
            rgb_array: HxWx3 RGB array (uint16)
            width: Image width
            height: Image height
            input_narrow_range: If True, input is narrow range (64-940 @12-bit, i.e., 4096-60160 @16-bit).
                              If False, input is full range (0-65535). Default: False
            output_narrow_range: If True, output is narrow range (256-3760).
                               If False, output is full range (0-4095). Default: False

        Returns:
            Flat uint8 array in 12-bit RGB format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_uint16_to_rgb12(rgb_array, width, height, input_narrow_range, output_narrow_range)

    def rgb_float_to_rgb12(rgb_array, width, height, output_narrow_range=False):
        """Convert RGB float numpy array to 12-bit RGB format.

        Automatically converts input array to C-contiguous layout if needed.

        Note: Float input is always interpreted as full range (0.0-1.0).

        Args:
            rgb_array: HxWx3 RGB array (float, 0.0-1.0 full range)
            width: Image width
            height: Image height
            output_narrow_range: If True, map 0.0-1.0 to 256-3760 (narrow range).
                               If False, map 0.0-1.0 to 0-4095 (full range). Default: False

        Returns:
            Flat uint8 array in 12-bit RGB format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_float_to_rgb12(rgb_array, width, height, output_narrow_range)

    # Unpacking functions (format -> RGB)
    def yuv10_to_rgb_uint16(yuv_array, width, height, matrix=Gamut.Rec709, input_narrow_range=True, output_narrow_range=False):
        """Convert 10-bit YUV (v210) to RGB uint16.

        Args:
            yuv_array: Flat uint8 array in v210 format
            width: Image width
            height: Image height
            matrix: Color matrix (Rec601, Rec709, or Rec2020)
            input_narrow_range: If True, input is narrow range (Y: 64-940, UV: 64-960). Default: True
            output_narrow_range: If True, output is narrow range (4096-60160 @16-bit). Default: False

        Returns:
            HxWx3 RGB array (uint16)
        """
        yuv_array = np.ascontiguousarray(yuv_array)
        return _yuv10_to_rgb_uint16(yuv_array, width, height, matrix, input_narrow_range, output_narrow_range)

    def yuv10_to_rgb_float(yuv_array, width, height, matrix=Gamut.Rec709, input_narrow_range=True):
        """Convert 10-bit YUV (v210) to RGB float.

        Args:
            yuv_array: Flat uint8 array in v210 format
            width: Image width
            height: Image height
            matrix: Color matrix (Rec601, Rec709, or Rec2020)
            input_narrow_range: If True, input is narrow range (Y: 64-940, UV: 64-960). Default: True

        Returns:
            HxWx3 RGB array (float, 0.0-1.0 full range)
        """
        yuv_array = np.ascontiguousarray(yuv_array)
        return _yuv10_to_rgb_float(yuv_array, width, height, matrix, input_narrow_range)

    def yuv8_to_rgb_uint16(yuv_array, width, height, matrix=Gamut.Rec709, input_narrow_range=True, output_narrow_range=False):
        """Convert 8-bit YUV (2vuy) to RGB uint16.

        Args:
            yuv_array: Flat uint8 array in 2vuy format
            width: Image width
            height: Image height
            matrix: Color matrix (Rec601, Rec709, or Rec2020)
            input_narrow_range: If True, input is narrow range (Y: 16-235, UV: 16-240). Default: True
            output_narrow_range: If True, output is narrow range (4096-60160 @16-bit). Default: False

        Returns:
            HxWx3 RGB array (uint16)
        """
        yuv_array = np.ascontiguousarray(yuv_array)
        return _yuv8_to_rgb_uint16(yuv_array, width, height, matrix, input_narrow_range, output_narrow_range)

    def yuv8_to_rgb_float(yuv_array, width, height, matrix=Gamut.Rec709, input_narrow_range=True):
        """Convert 8-bit YUV (2vuy) to RGB float.

        Args:
            yuv_array: Flat uint8 array in 2vuy format
            width: Image width
            height: Image height
            matrix: Color matrix (Rec601, Rec709, or Rec2020)
            input_narrow_range: If True, input is narrow range (Y: 16-235, UV: 16-240). Default: True

        Returns:
            HxWx3 RGB array (float, 0.0-1.0 full range)
        """
        yuv_array = np.ascontiguousarray(yuv_array)
        return _yuv8_to_rgb_float(yuv_array, width, height, matrix, input_narrow_range)

    def rgb10_to_uint16(rgb_array, width, height, input_narrow_range=True, output_narrow_range=False):
        """Convert 10-bit RGB (R10l) to RGB uint16.

        Args:
            rgb_array: Flat uint8 array in R10l format
            width: Image width
            height: Image height
            input_narrow_range: If True, input is narrow range (64-940 @10-bit). Default: True
            output_narrow_range: If True, output is narrow range (4096-60160 @16-bit). Default: False

        Returns:
            HxWx3 RGB array (uint16)
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb10_to_uint16(rgb_array, width, height, input_narrow_range, output_narrow_range)

    def rgb10_to_float(rgb_array, width, height, input_narrow_range=True):
        """Convert 10-bit RGB (R10l) to RGB float.

        Args:
            rgb_array: Flat uint8 array in R10l format
            width: Image width
            height: Image height
            input_narrow_range: If True, input is narrow range (64-940 @10-bit). Default: True

        Returns:
            HxWx3 RGB array (float, 0.0-1.0 full range)
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb10_to_float(rgb_array, width, height, input_narrow_range)

    def rgb12_to_uint16(rgb_array, width, height, input_narrow_range=False, output_narrow_range=False):
        """Convert 12-bit RGB (R12L) to RGB uint16.

        Args:
            rgb_array: Flat uint8 array in R12L format
            width: Image width
            height: Image height
            input_narrow_range: If True, input is narrow range (256-3760 @12-bit). Default: False
            output_narrow_range: If True, output is narrow range (4096-60160 @16-bit). Default: False

        Returns:
            HxWx3 RGB array (uint16)
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb12_to_uint16(rgb_array, width, height, input_narrow_range, output_narrow_range)

    def rgb12_to_float(rgb_array, width, height, input_narrow_range=False):
        """Convert 12-bit RGB (R12L) to RGB float.

        Args:
            rgb_array: Flat uint8 array in R12L format
            width: Image width
            height: Image height
            input_narrow_range: If True, input is narrow range (256-3760 @12-bit). Default: False

        Returns:
            HxWx3 RGB array (float, 0.0-1.0 full range)
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb12_to_float(rgb_array, width, height, input_narrow_range)

    # Unpacking functions (format -> components)
    def unpack_v210(yuv_array, width, height):
        """Unpack 10-bit YUV (v210) to separate Y, Cb, Cr arrays.

        Args:
            yuv_array: Flat uint8 array in v210 format
            width: Image width
            height: Image height

        Returns:
            Dictionary with 'y', 'cb', 'cr' keys, each containing HxW uint16 array (10-bit values)
        """
        yuv_array = np.ascontiguousarray(yuv_array)
        return _unpack_v210(yuv_array, width, height)

    def unpack_2vuy(yuv_array, width, height):
        """Unpack 8-bit YUV (2vuy) to separate Y, Cb, Cr arrays.

        Args:
            yuv_array: Flat uint8 array in 2vuy format
            width: Image width
            height: Image height

        Returns:
            Dictionary with 'y', 'cb', 'cr' keys, each containing HxW uint8 array
        """
        yuv_array = np.ascontiguousarray(yuv_array)
        return _unpack_2vuy(yuv_array, width, height)

    def unpack_rgb10(rgb_array, width, height):
        """Unpack 10-bit RGB (R10l) to separate R, G, B arrays.

        Args:
            rgb_array: Flat uint8 array in R10l format
            width: Image width
            height: Image height

        Returns:
            Dictionary with 'r', 'g', 'b' keys, each containing HxW uint16 array (10-bit values)
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _unpack_rgb10(rgb_array, width, height)

    def unpack_rgb12(rgb_array, width, height):
        """Unpack 12-bit RGB (R12L) to separate R, G, B arrays.

        Args:
            rgb_array: Flat uint8 array in R12L format
            width: Image width
            height: Image height

        Returns:
            Dictionary with 'r', 'g', 'b' keys, each containing HxW uint16 array (12-bit values)
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _unpack_rgb12(rgb_array, width, height)

except ImportError:
    # C++ extension not built yet
    pass

__version__ = "0.16.0b0"
__author__ = "Nick Shaw"

__all__ = [
    # High-level API
    "BlackmagicOutput",
    "BlackmagicInput",
    "DisplayMode",
    "PixelFormat",
    "Matrix",
    "Eotf",
    "InputConnection",
    "create_test_pattern",
    # Low-level API
    "DeckLinkOutput",
    "DeckLinkInput",
    "VideoSettings",
    "HdrMetadataCustom",
    "DisplayModeInfo",
    "CapturedFrame",
    "DeviceCapabilities",
    "Gamut",
    # Device utilities
    "get_device_capabilities",
    # Conversion utilities - Packing (RGB -> format)
    "rgb_to_bgra",
    "rgb_uint8_to_yuv8",
    "rgb_uint16_to_yuv8",
    "rgb_float_to_yuv8",
    "rgb_uint16_to_yuv10",
    "rgb_float_to_yuv10",
    "rgb_uint16_to_rgb10",
    "rgb_float_to_rgb10",
    "rgb_uint16_to_rgb12",
    "rgb_float_to_rgb12",
    # Conversion utilities - Unpacking (format -> RGB)
    "yuv10_to_rgb_uint16",
    "yuv10_to_rgb_float",
    "yuv8_to_rgb_uint16",
    "yuv8_to_rgb_float",
    "rgb10_to_uint16",
    "rgb10_to_float",
    "rgb12_to_uint16",
    "rgb12_to_float",
    # Conversion utilities - Unpacking (format -> components)
    "unpack_v210",
    "unpack_2vuy",
    "unpack_rgb10",
    "unpack_rgb12",
]
