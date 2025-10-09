#!/usr/bin/env python3
"""
Test 12-bit RGB color bars output

This script tests the RGB12 pixel format by displaying color bars
in 12-bit RGB format (full range only).
"""

import numpy as np
import time
from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat


def create_colorbars_float(width, height):
    """
    Create 75% color bars as float32 (0.0-1.0 range)

    Returns RGB array with shape (height, width, 3), dtype float32
    """
    frame = np.zeros((height, width, 3), dtype=np.float32)

    # 75% color bars (100% saturation but 75% luminance)
    # Top 2/3: Color bars
    # Bottom 1/3: Additional test patterns

    bar_width = width // 7
    top_height = int(height * 2 / 3)

    # Define 75% amplitude colors (RGB in 0.0-1.0 range)
    colors_top = [
        [0.75, 0.75, 0.75],  # 75% White
        [0.75, 0.75, 0.00],  # Yellow
        [0.00, 0.75, 0.75],  # Cyan
        [0.00, 0.75, 0.00],  # Green
        [0.75, 0.00, 0.75],  # Magenta
        [0.75, 0.00, 0.00],  # Red
        [0.00, 0.00, 0.75],  # Blue
    ]

    # Top 2/3: Main color bars
    for i in range(7):
        x_start = i * bar_width
        x_end = (i + 1) * bar_width if i < 6 else width
        frame[:top_height, x_start:x_end] = colors_top[i]

    # Bottom 1/3: Additional test patterns
    bottom_start = top_height

    # Left section: 75% Blue
    section_width = width // 3
    frame[bottom_start:, 0:section_width] = [0.00, 0.00, 0.75]  # Blue

    # Middle section: Black to white ramp
    for x in range(section_width, 2 * section_width):
        level = (x - section_width) / section_width
        frame[bottom_start:, x] = [level, level, level]

    # Right section: 0%, 7.5%, 15% blacks/grays
    pluge_width = (width - 2 * section_width) // 3
    pluge_start = 2 * section_width

    # Black (0%)
    frame[bottom_start:, pluge_start:pluge_start + pluge_width] = [0.0, 0.0, 0.0]

    # 7.5% gray
    frame[bottom_start:, pluge_start + pluge_width:pluge_start + 2 * pluge_width] = [0.075, 0.075, 0.075]

    # 15% gray
    frame[bottom_start:, pluge_start + 2 * pluge_width:] = [0.15, 0.15, 0.15]

    return frame


def create_colorbars_uint16(width, height):
    """
    Create 75% color bars as uint16 (0-65535 range)

    Returns RGB array with shape (height, width, 3), dtype uint16
    """
    # Create float version first
    frame_float = create_colorbars_float(width, height)

    # Convert to uint16 (clamp to 0.0-1.0)
    frame_float = np.clip(frame_float, 0.0, 1.0)
    frame_uint16 = (frame_float * 65535).astype(np.uint16)

    return frame_uint16


def test_rgb12_float():
    """Test RGB12 output with float data (full range 0-4095)"""
    print("Test 1: RGB12 Color Bars - Float Input, Full Range (0-4095)")
    print("=" * 70)

    with BlackmagicOutput() as output:
        devices = output.get_available_devices()
        print(f"Available devices: {devices}")

        if not devices:
            print("No DeckLink devices found!")
            return False

        if not output.initialize(device_index=0):
            print("Failed to initialize device")
            return False

        print("Device initialized successfully")

        # Get display mode info
        mode_info = output.get_display_mode_info(DisplayMode.HD1080p25)
        width, height = mode_info['width'], mode_info['height']
        print(f"Display mode: {width}x{height} @ {mode_info['framerate']}fps")

        # Create color bars in float format
        print("Creating 75% color bars (float32, 0.0-1.0 range)...")
        frame = create_colorbars_float(width, height)
        print(f"Frame: dtype={frame.dtype}, shape={frame.shape}, range=[{frame.min():.3f}, {frame.max():.3f}]")

        # Display with RGB12 (full range only)
        print("Displaying with RGB12 pixel format (full range: 0.0-1.0 → 0-4095)...")
        if output.display_static_frame(
            frame,
            DisplayMode.HD1080p25,
            PixelFormat.RGB12
        ):
            print("✓ Color bars displayed successfully")
            print("  Press Ctrl+C to continue to next test...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n")
                return True
        else:
            print("✗ Failed to display frame")
            return False


def test_rgb12_uint16():
    """Test RGB12 output with uint16 data (bit-shifted)"""
    print("Test 2: RGB12 Color Bars - uint16 Input (bit-shifted 16→12)")
    print("=" * 70)

    with BlackmagicOutput() as output:
        if not output.initialize(device_index=0):
            print("Failed to initialize device")
            return False

        # Get display mode info
        mode_info = output.get_display_mode_info(DisplayMode.HD1080p25)
        width, height = mode_info['width'], mode_info['height']

        # Create color bars in uint16 format
        print("Creating 75% color bars (uint16, 0-65535 range)...")
        frame = create_colorbars_uint16(width, height)
        print(f"Frame: dtype={frame.dtype}, shape={frame.shape}, range=[{frame.min()}, {frame.max()}]")

        # Display with RGB12 (automatically bit-shifted)
        print("Displaying with RGB12 pixel format (bit-shift: uint16 >> 4)...")
        if output.display_static_frame(
            frame,
            DisplayMode.HD1080p25,
            PixelFormat.RGB12
        ):
            print("✓ Color bars displayed successfully")
            print("  Press Ctrl+C to continue to next test...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n")
                return True
        else:
            print("✗ Failed to display frame")
            return False


def test_rgb12_comparison():
    """Compare RGB12 with RGB10 and YUV10 output"""
    print("Test 3: Comparison - RGB12 vs RGB10 vs YUV10")
    print("=" * 70)

    with BlackmagicOutput() as output:
        if not output.initialize(device_index=0):
            print("Failed to initialize device")
            return False

        # Get display mode info
        mode_info = output.get_display_mode_info(DisplayMode.HD1080p25)
        width, height = mode_info['width'], mode_info['height']

        # Create color bars
        frame = create_colorbars_float(width, height)

        # Display with RGB12
        print("\nDisplaying with RGB12 (full range)...")
        if output.display_static_frame(
            frame,
            DisplayMode.HD1080p25,
            PixelFormat.RGB12
        ):
            print("✓ RGB12 displayed - Press Ctrl+C to switch to RGB10...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("✗ Failed to display RGB12")
            return False

        # Display with RGB10
        print("\nDisplaying with RGB10 (full range)...")
        if output.display_static_frame(
            frame,
            DisplayMode.HD1080p25,
            PixelFormat.RGB10,
            video_range=False
        ):
            print("✓ RGB10 displayed - Press Ctrl+C to switch to YUV10...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("✗ Failed to display RGB10")
            return False

        # Display with YUV10
        print("\nDisplaying with YUV10 (video range, Rec.709)...")
        if output.display_static_frame(
            frame,
            DisplayMode.HD1080p25,
            PixelFormat.YUV10
        ):
            print("✓ YUV10 displayed - Press Ctrl+C to stop...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n")
                return True
        else:
            print("✗ Failed to display YUV10")
            return False


def main():
    """Main test function"""
    print("\n" + "=" * 70)
    print("12-bit RGB Color Bars Test Suite")
    print("=" * 70)
    print()

    tests = [
        ("RGB12 - Float Input (Full Range)", test_rgb12_float),
        ("RGB12 - uint16 Input (bit-shifted)", test_rgb12_uint16),
        ("RGB12 vs RGB10 vs YUV10 Comparison", test_rgb12_comparison),
    ]

    print("Available tests:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"  {i}. {name}")
    print("  0. Run all tests")
    print()

    try:
        choice = input("Select test (0-3): ").strip()
        print()

        if choice == "0":
            # Run all tests
            results = []
            for name, test_func in tests:
                print(f"\n{'='*70}")
                result = test_func()
                results.append((name, result))
                print()

            # Summary
            print("\n" + "=" * 70)
            print("Test Summary:")
            print("=" * 70)
            for name, result in results:
                status = "✓ PASSED" if result else "✗ FAILED"
                print(f"{status}: {name}")

        elif choice.isdigit() and 1 <= int(choice) <= len(tests):
            idx = int(choice) - 1
            name, test_func = tests[idx]
            test_func()
        else:
            print("Invalid choice")

    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
