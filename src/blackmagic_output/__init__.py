"""
Blackmagic DeckLink Output Library

A Python library for outputting video frames to Blackmagic DeckLink devices.
Supports static frame output, dynamic updates, HDR, and timecode.
"""

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
        Timecode,
        Gamut,
        Eotf as _Eotf,
        Matrix as _Matrix,
        rgb_to_bgra,
        rgb_uint16_to_yuv10,
        rgb_float_to_yuv10,
    )
except ImportError:
    # C++ extension not built yet
    pass

__version__ = "1.0.0"
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
    "Timecode",
    "Gamut",
    # Conversion utilities
    "rgb_to_bgra",
    "rgb_uint16_to_yuv10",
    "rgb_float_to_yuv10",
]
