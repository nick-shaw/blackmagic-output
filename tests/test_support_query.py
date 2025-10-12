#!/usr/bin/env python3
"""
Test script for checking display mode and pixel format support
"""

from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat

def main():
    output = BlackmagicOutput()

    if not output.initialize():
        print("Failed to initialize DeckLink device")
        return

    print("Testing display mode support:")
    print("=" * 60)

    test_modes = [
        DisplayMode.HD1080p25,
        DisplayMode.HD1080p50,
        DisplayMode.Mode4K2160p25,
        DisplayMode.Mode4K2160p50,
        DisplayMode.Mode8K4320p25,
    ]

    for mode in test_modes:
        supported = output.is_display_mode_supported(mode)
        status = "✓ Supported" if supported else "✗ Not supported"
        print(f"{mode.name:30} {status}")

    print("\n" + "=" * 60)
    print("Testing pixel format support for HD1080p25:")
    print("=" * 60)

    test_formats = [
        PixelFormat.BGRA,
        PixelFormat.YUV,
        PixelFormat.YUV10,
        PixelFormat.RGB10,
        PixelFormat.RGB12,
    ]

    for fmt in test_formats:
        supported = output.is_pixel_format_supported(DisplayMode.HD1080p25, fmt)
        status = "✓ Supported" if supported else "✗ Not supported"
        print(f"{fmt.name:30} {status}")

    output.cleanup()

if __name__ == "__main__":
    main()
