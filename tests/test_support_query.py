#!/usr/bin/env python3
"""
Test script for checking display mode and pixel format support
"""

from blackmagic_io import BlackmagicOutput, DisplayMode, PixelFormat

def main():
    output = BlackmagicOutput()

    if not output.initialize():
        print("Failed to initialize DeckLink device")
        return

    print("Testing pixel format support for various display modes:")
    print("=" * 60)

    test_modes = [
        DisplayMode.HD1080p25,
        DisplayMode.HD1080p50,
        DisplayMode.Mode4K2160p25,
         DisplayMode.Mode4K2160p50,
    ]

    test_formats = [
        PixelFormat.BGRA,
        PixelFormat.YUV10,
        PixelFormat.RGB10,
        PixelFormat.RGB12,
    ]

    for mode in test_modes:
        print(f"\n{mode.name}:")
        for fmt in test_formats:
            supported = output.is_pixel_format_supported(mode, fmt)
            status = "✓" if supported else "✗"
            print(f"  {status} {fmt.name}")

    output.cleanup()

if __name__ == "__main__":
    main()
