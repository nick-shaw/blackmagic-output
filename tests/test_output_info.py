#!/usr/bin/env python3
"""
Test script to query and display current output configuration.
"""

import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat


def create_simple_colorbars(width, height):
    """Create simple 100% color bars (8 patches)."""
    frame = np.zeros((height, width, 3), dtype=np.float32)

    bar_width = width // 8
    colors = [
        [1.0, 1.0, 1.0],  # White
        [1.0, 1.0, 0.0],  # Yellow
        [0.0, 1.0, 1.0],  # Cyan
        [0.0, 1.0, 0.0],  # Green
        [1.0, 0.0, 1.0],  # Magenta
        [1.0, 0.0, 0.0],  # Red
        [0.0, 0.0, 1.0],  # Blue
        [0.0, 0.0, 0.0],  # Black
    ]

    for i in range(8):
        x_start = i * bar_width
        x_end = (i + 1) * bar_width if i < 7 else width
        frame[:, x_start:x_end] = colors[i]

    return frame


def test_output_info(pixel_format, narrow_range=None):
    """Test querying output info for a given pixel format."""

    with BlackmagicOutput() as output:
        devices = output.get_available_devices()
        if not devices:
            print("No DeckLink devices found!")
            return False

        if not output.initialize(device_index=0):
            print("Failed to initialize device")
            return False

        # Get display mode info
        mode_info = output.get_display_mode_info(DisplayMode.HD1080p25)
        width, height = mode_info['width'], mode_info['height']

        # Create color bars
        frame = create_simple_colorbars(width, height)

        # Display with specified pixel format
        kwargs = {'narrow_range': narrow_range} if narrow_range is not None else {}
        if output.display_static_frame(
            frame,
            DisplayMode.HD1080p25,
            pixel_format,
            **kwargs
        ):
            # Query the current output configuration
            info = output.get_current_output_info()

            print(f"\n{'='*70}")
            print(f"Current Output Configuration:")
            print(f"{'='*70}")
            print(f"Display Mode:      {info['display_mode_name']}")
            print(f"Pixel Format:      {info['pixel_format_name']}")
            print(f"Resolution:        {info['width']}x{info['height']}")
            print(f"Frame Rate:        {info['framerate']:.2f} fps")
            print(f"RGB 4:4:4 Mode:    {'Enabled' if info['rgb444_mode_enabled'] else 'Disabled'}")
            print(f"{'='*70}\n")

            # Keep displaying until user presses Enter
            input("Color bars are displaying. Press Enter to continue...")

            return True
        else:
            print("Failed to display frame")
            return False


def main():
    """Main test function."""
    print("\n" + "="*70)
    print("Output Configuration Query Test")
    print("="*70)
    print()

    tests = [
        ("YUV10", PixelFormat.YUV10, None),
        ("RGB10 (narrow range)", PixelFormat.RGB10, True),
        ("RGB10 (full range)", PixelFormat.RGB10, False),
        ("RGB12", PixelFormat.RGB12, None),
    ]

    print("This test will display 100% color bars in each format")
    print("and query the current output configuration.\n")

    try:
        for name, pixel_format, narrow_range in tests:
            print(f"Testing {name}...")
            if not test_output_info(pixel_format, narrow_range):
                print(f"✗ Failed to test {name}")
            print()

        print("\n" + "="*70)
        print("All tests completed!")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
