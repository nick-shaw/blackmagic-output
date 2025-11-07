"""
Blackmagic DeckLink Output Library

A Python library for outputting video frames to Blackmagic DeckLink devices.
Supports static frame output, dynamic updates, and HDR.
"""

import numpy as np

from .blackmagic_output import (
    BlackmagicOutput,
    DisplayMode,
    PixelFormat,
    Matrix,
    Eotf,
    create_test_pattern,
)

# Re-export low-level API for advanced use
try:
    import decklink_output
    from decklink_output import (
        DeckLinkOutput,
        VideoSettings,
        HdrMetadataCustom,
        Gamut,
        Eotf as _Eotf,
        Matrix as _Matrix,
    )
    # Import C++ conversion functions with underscore prefix
    from decklink_output import (
        rgb_to_bgra as _rgb_to_bgra,
        rgb_uint16_to_yuv10 as _rgb_uint16_to_yuv10,
        rgb_float_to_yuv10 as _rgb_float_to_yuv10,
        rgb_uint16_to_rgb10 as _rgb_uint16_to_rgb10,
        rgb_float_to_rgb10 as _rgb_float_to_rgb10,
        rgb_uint16_to_rgb12 as _rgb_uint16_to_rgb12,
        rgb_float_to_rgb12 as _rgb_float_to_rgb12,
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

    def rgb_uint16_to_rgb10(rgb_array, width, height):
        """Convert RGB uint16 numpy array to 10-bit RGB r210 format.

        Automatically converts input array to C-contiguous layout if needed.

        Args:
            rgb_array: HxWx3 RGB array (uint16)
            width: Image width
            height: Image height

        Returns:
            Flat uint8 array in r210 format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_uint16_to_rgb10(rgb_array, width, height)

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

    def rgb_uint16_to_rgb12(rgb_array, width, height):
        """Convert RGB uint16 numpy array to 12-bit RGB format.

        Automatically converts input array to C-contiguous layout if needed.

        Args:
            rgb_array: HxWx3 RGB array (uint16)
            width: Image width
            height: Image height

        Returns:
            Flat uint8 array in 12-bit RGB format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_uint16_to_rgb12(rgb_array, width, height)

    def rgb_float_to_rgb12(rgb_array, width, height):
        """Convert RGB float numpy array to 12-bit RGB format.

        Automatically converts input array to C-contiguous layout if needed.

        Args:
            rgb_array: HxWx3 RGB array (float, 0.0-1.0 range)
            width: Image width
            height: Image height

        Returns:
            Flat uint8 array in 12-bit RGB format
        """
        rgb_array = np.ascontiguousarray(rgb_array)
        return _rgb_float_to_rgb12(rgb_array, width, height)

except ImportError:
    # C++ extension not built yet
    pass

__version__ = "0.14.0b0"
__author__ = "Nick Shaw"

__all__ = [
    # High-level API
    "BlackmagicOutput",
    "DisplayMode",
    "PixelFormat",
    "Matrix",
    "Eotf",
    "create_test_pattern",
    # Low-level API
    "DeckLinkOutput",
    "VideoSettings",
    "HdrMetadataCustom",
    "Gamut",
    # Conversion utilities
    "rgb_to_bgra",
    "rgb_uint16_to_yuv10",
    "rgb_float_to_yuv10",
    "rgb_uint16_to_rgb10",
    "rgb_float_to_rgb10",
    "rgb_uint16_to_rgb12",
    "rgb_float_to_rgb12",
]
