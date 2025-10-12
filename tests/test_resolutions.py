#!/usr/bin/env python3
"""Test dynamic resolution support by outputting test images in various resolutions"""

import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode
import time

# Test getting info for different resolutions
test_modes = [
    DisplayMode.HD1080p25,
    DisplayMode.HD720p60,
    DisplayMode.Mode4K2160p30,
    DisplayMode.Mode8K4320p25,
    DisplayMode.NTSC,
    DisplayMode.Mode2560x1440p60,
]

print("Testing dynamic resolution support with hardware output:\n")

output = BlackmagicOutput()

# Initialize hardware
if not output.initialize(device_index=0):
    print("ERROR: Failed to initialize DeckLink device")
    print("Make sure a DeckLink device is connected.")
    exit(1)

print("✓ DeckLink device initialized\n")
print("Testing resolutions:\n")

for mode in test_modes:
    try:
        # Get resolution info
        info = output.get_display_mode_info(mode)
        width = info['width']
        height = info['height']
        framerate = info['framerate']

        print(f"{mode.name:20s} -> {width:4d}x{height:4d} @ {framerate:6.2f}fps", end=" ... ")

        # Create a simple test pattern (color bars)
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Create vertical color bars
        bar_width = width // 8
        colors = [
            [255, 255, 255],  # White
            [255, 255, 0],    # Yellow
            [0, 255, 255],    # Cyan
            [0, 255, 0],      # Green
            [255, 0, 255],    # Magenta
            [255, 0, 0],      # Red
            [0, 0, 255],      # Blue
            [0, 0, 0]         # Black
        ]

        for i, color in enumerate(colors):
            x_start = i * bar_width
            x_end = min((i + 1) * bar_width, width)
            frame[:, x_start:x_end] = color

        # Try to display the frame
        if output.display_static_frame(frame, mode):
            time.sleep(1.0)  # Let hardware settle after mode change
            print("✓ OK")
            time.sleep(3)  # Display for 3 seconds

            # Fully stop and cleanup before next resolution
            output.stop()
            time.sleep(1.0)  # Give hardware time to fully stop
        else:
            print("✗ FAILED (mode not supported by hardware)")

    except Exception as e:
        print(f"✗ ERROR: {e}")

# Final cleanup
output.cleanup()

print("\nTest complete!")
