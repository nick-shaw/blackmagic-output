#!/usr/bin/env python3
"""
DeckLink Device Diagnostic Script

This script helps diagnose DeckLink device availability and capabilities.
"""

import numpy as np
from blackmagic_output import BlackmagicOutput, PixelFormat, DisplayMode
import decklink_output

def test_device_detection():
    """Test basic device detection and listing."""
    print("=== DeckLink Device Detection ===")

    output = BlackmagicOutput()

    # Test device listing
    try:
        devices = output.get_available_devices()
        print(f"Found {len(devices)} DeckLink device(s):")
        for i, device_name in enumerate(devices):
            print(f"  [{i}] {device_name}")

        if not devices:
            print("No DeckLink devices found!")
            print("Possible causes:")
            print("  - No DeckLink hardware connected")
            print("  - DeckLink drivers not installed")
            print("  - Device in use by another application")
            return False

    except Exception as e:
        print(f"Error getting device list: {e}")
        return False

    return len(devices) > 0

def test_device_initialization():
    """Test device initialization for each available device."""
    print("\n=== Device Initialization Test ===")

    output = BlackmagicOutput()
    devices = output.get_available_devices()

    for i, device_name in enumerate(devices):
        print(f"\nTesting device [{i}]: {device_name}")

        test_output = BlackmagicOutput()
        if test_output.initialize(device_index=i):
            print(f"Device [{i}] initialized successfully")

            try:
                mode_info = test_output.get_display_mode_info(DisplayMode.HD1080p25)
                print(f"   HD1080p25 info: {mode_info}")
            except Exception as e:
                print(f"   Could not get display mode info: {e}")

            test_output.cleanup()
        else:
            print(f"Device [{i}] failed to initialize")
            print("   This device may not support video output")

def test_output_setup():
    """Test output setup with different pixel formats using low-level API."""
    print("\n=== Output Setup Test ===")

    # Use low-level API for setup testing without displaying
    output = decklink_output.DeckLinkOutput()
    if not output.initialize(0):
        print("Could not initialize any device for output test")
        return

    formats_to_test = [
        (decklink_output.PixelFormat.BGRA, "8-bit BGRA"),
        (decklink_output.PixelFormat.YUV, "8-bit YUV"),
        (decklink_output.PixelFormat.YUV10, "10-bit YUV (v210)")
    ]

    for pixel_format, format_name in formats_to_test:
        print(f"\nTesting {format_name}:")
        try:
            settings = output.get_video_settings(decklink_output.DisplayMode.HD1080p25)
            settings.format = pixel_format
            success = output.setup_output(settings)
            if success:
                print(f"{format_name} setup successful")
            else:
                print(f"{format_name} setup failed")
        except Exception as e:
            print(f"{format_name} setup error: {e}")

    output.cleanup()

def test_frame_conversion():
    """Test RGB to various format conversions without hardware."""
    print("\n=== Frame Conversion Test ===")

    # Create test RGB frame
    width, height = 1920, 1080
    rgb_frame = np.zeros((height, width, 3), dtype=np.uint8)
    rgb_frame[:, :, 0] = 128  # Red
    rgb_frame[:, :, 1] = 64   # Green
    rgb_frame[:, :, 2] = 192  # Blue

    try:
        import decklink_output as _decklink

        print("Testing RGB to BGRA conversion...")
        bgra_frame = _decklink.rgb_to_bgra(rgb_frame, width, height)
        print(f"BGRA conversion: {bgra_frame.shape}, dtype: {bgra_frame.dtype}")

        print("Testing RGB uint8 to 10-bit YUV conversion...")
        rgb_uint16 = (rgb_frame.astype(np.uint16) << 8) | rgb_frame
        yuv10_frame = _decklink.rgb_uint16_to_yuv10(rgb_uint16, width, height)
        print(f"YUV10 conversion: {yuv10_frame.shape}, dtype: {yuv10_frame.dtype}")
        print(f"   Expected size: {((width + 5) // 6) * 16 * height} bytes")
        print(f"   Actual size: {yuv10_frame.size} bytes")

    except Exception as e:
        print(f"Frame conversion error: {e}")

def main():
    """Run all diagnostic tests."""
    print("DeckLink Diagnostic Tool")
    print("=" * 50)

    # Test 1: Device detection
    devices_found = test_device_detection()

    if devices_found:
        # Test 2: Device initialization
        test_device_initialization()

        # Test 3: Output setup
        test_output_setup()

    # Test 4: Frame conversion (works without hardware)
    test_frame_conversion()

    print("\n" + "=" * 50)
    print("Diagnostic complete!")

    if not devices_found:
        print("\nTroubleshooting steps:")
        print("1. Check that DeckLink hardware is connected")
        print("2. Verify DeckLink drivers are installed")
        print("3. Close other applications using DeckLink devices")
        print("4. Try running as administrator/sudo if needed")
        print("5. Check System Information for DeckLink devices")

if __name__ == "__main__":
    main()