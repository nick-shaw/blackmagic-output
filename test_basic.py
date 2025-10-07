#!/usr/bin/env python3
"""
Basic test for Blackmagic DeckLink Python Output Library
Tests device enumeration and basic API functionality.
"""

import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode, create_test_pattern

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

def test_display_modes():
    """Test display mode information"""
    print("\nTesting display mode information...")
    
    output = BlackmagicOutput()
    modes = [
        DisplayMode.HD1080p25,
        DisplayMode.HD1080p30, 
        DisplayMode.HD1080p50,
        DisplayMode.HD1080p60,
        DisplayMode.HD720p50,
        DisplayMode.HD720p60
    ]
    
    for mode in modes:
        info = output.get_display_mode_info(mode)
        print(f"  {mode.name}: {info['width']}x{info['height']} @ {info['framerate']}fps")

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
    
    output = BlackmagicOutput()
    success = output.initialize(device_index=0)
    
    if not success:
        print("  Initialization failed (expected if no hardware present)")
    else:
        print("  Initialization succeeded!")
        
        # Test setup without actually starting output
        try:
            settings_success = output.setup_output(DisplayMode.HD1080p25)
            if settings_success:
                print("  Setup succeeded!")
            else:
                print("  Setup failed (may be expected)")
        except Exception as e:
            print(f"  Setup exception: {e}")
        
        output.cleanup()

def main():
    """Run all basic tests"""
    print("Blackmagic DeckLink Python Output Library - Basic Tests")
    print("=" * 60)
    
    try:
        # Test 1: Device enumeration
        has_devices = test_device_enumeration()
        
        # Test 2: Display modes
        test_display_modes()
        
        # Test 3: Test patterns
        test_test_patterns()
        
        # Test 4: Initialization
        test_initialization_without_hardware()
        
        print("\n" + "=" * 60)
        print("Basic tests completed successfully!")
        
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