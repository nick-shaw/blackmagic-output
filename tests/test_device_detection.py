#!/usr/bin/env python3
"""
Device Detection Test for Blackmagic DeckLink Python Output Library
Tests device enumeration and detection functionality.
"""

import sys
import numpy as np
from blackmagic_output import BlackmagicOutput, create_test_pattern
import decklink_output

def test_device_enumeration():
    """Test device enumeration"""
    print("Testing device enumeration...")
    
    output = BlackmagicOutput()
    devices = output.get_available_devices()
    
    print(f"Found {len(devices)} DeckLink devices:")
    for i, device in enumerate(devices):
        print(f"  {i}: {device}")
    
    if len(devices) == 0:
        print("No DeckLink devices found. This is expected if no hardware is connected.")
        return False
    else:
        return True

def test_display_modes(max_modes=5):
    """Test available display modes for each device

    Args:
        max_modes: Maximum number of modes to display per device (int or 'all')
    """
    print("\nTesting available display modes...")

    output = BlackmagicOutput()
    devices = output.get_available_devices()

    if not devices:
        print("  No devices available to query display modes")
        return

    for device_idx, device_name in enumerate(devices):
        print(f"\n  Device [{device_idx}]: {device_name}")

        # Initialize this device
        test_output = BlackmagicOutput()
        if not test_output.initialize(device_idx):
            print(f"    Could not initialize device")
            continue

        # Query supported display modes directly from device
        try:
            modes = test_output.get_supported_display_modes()
            supported_modes = [
                f"{mode['name']} ({mode['width']}x{mode['height']} @ {mode['framerate']:.2f}fps)"
                for mode in modes
            ]
        except Exception as e:
            print(f"    Error querying display modes: {e}")
            test_output.cleanup()
            continue

        if supported_modes:
            print(f"    Supported display modes: {len(supported_modes)}")

            # Determine how many to show
            if max_modes == 'all':
                modes_to_show = supported_modes
            else:
                modes_to_show = supported_modes[:max_modes]

            for mode_info in modes_to_show:
                print(f"      - {mode_info}")

            if max_modes != 'all' and len(supported_modes) > max_modes:
                print(f"      ... and {len(supported_modes) - max_modes} more")
        else:
            print(f"    Could not detect supported display modes")

        test_output.cleanup()

def test_test_patterns():
    """Test pattern creation"""
    print("\nTesting test pattern creation...")
    
    patterns = ['gradient', 'bars', 'checkerboard']
    width, height = 1920, 1080
    
    for pattern in patterns:
        frame = create_test_pattern(width, height, pattern)
        print(f"  Created {pattern} pattern: {frame.shape}, dtype={frame.dtype}")
        
        # Check that pattern has some variation (not all zeros)
        if np.sum(frame) > 0:
            print(f"    Pattern has data (sum={np.sum(frame)})")
        else:
            print(f"    Warning: Pattern appears to be empty")

def test_initialization_without_hardware():
    """Test initialization behavior when no hardware is present"""
    print("\nTesting initialization without hardware...")

    # Use low-level API for setup testing without displaying
    output = decklink_output.DeckLinkOutput()
    success = output.initialize(0)

    if not success:
        print("  Initialization failed (expected if no hardware present)")
    else:
        print("  Initialization succeeded!")

        # Test setup without actually starting output
        try:
            settings = output.get_video_settings(decklink_output.DisplayMode.HD1080p25)
            settings.format = decklink_output.PixelFormat.YUV10
            settings_success = output.setup_output(settings)
            if settings_success:
                print("  Setup succeeded!")
            else:
                print("  Setup failed (may be expected)")
        except Exception as e:
            print(f"  Setup exception: {e}")

        output.cleanup()

def main():
    """Run all device detection tests"""
    # Parse command line arguments
    max_modes = 5  # Default
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'all':
            max_modes = 'all'
        else:
            try:
                max_modes = int(sys.argv[1])
            except ValueError:
                print(f"Invalid argument: {sys.argv[1]}")
                print("Usage: python test_device_detection.py [max_modes|all]")
                print("  max_modes: Number of display modes to show per device (default: 5)")
                print("  all: Show all supported display modes")
                sys.exit(1)

    print("Blackmagic DeckLink Python Output Library - Device Detection Tests")
    print("=" * 70)

    try:
        # Test 1: Device enumeration
        has_devices = test_device_enumeration()

        # Test 2: Display modes
        test_display_modes(max_modes)

        # Test 3: Test patterns
        test_test_patterns()

        # Test 4: Initialization
        test_initialization_without_hardware()

        print("\n" + "=" * 70)
        print("Device detection tests completed successfully!")

        if has_devices:
            print("\nTo test actual video output, run:")
            print("python example_usage.py")
        else:
            print("\nNo DeckLink devices found. Connect a DeckLink device to test video output.")

    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()