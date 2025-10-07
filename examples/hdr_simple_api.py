#!/usr/bin/env python3
"""
Example: HDR Output with Simplified API

Demonstrates the simplified display_static_frame() API with matrix and hdr_metadata
parameters, eliminating the need to call set_hdr_metadata() separately.
"""

import sys
import numpy as np
sys.path.insert(0, '../src')

import blackmagic_output as bmo

def main():
    # Create output instance
    output = bmo.BlackmagicOutput()

    # Initialize device
    if not output.initialize(device_index=0):
        print("Failed to initialize DeckLink device")
        return

    # Create HDR test frame (10-bit linear light values, normalized 0.0-1.0)
    # For PQ, these values should be in linear light before PQ encoding
    width, height = 1920, 1080
    frame = np.ones((height, width, 3), dtype=np.float32)

    # Create a gradient to see the HDR effect
    for y in range(height):
        intensity = y / height  # 0.0 to 1.0
        frame[y, :, :] = intensity

    print("Displaying HDR PQ frame with Rec.2020 matrix...")

    # Simple API: matrix and HDR metadata in one call
    success = output.display_static_frame(
        frame,
        bmo.DisplayMode.HD1080p25,
        pixel_format=bmo.PixelFormat.YUV10,
        matrix=bmo.Matrix.Rec2020,           # Use Rec.2020 matrix for conversion
        hdr_metadata={'eotf': bmo.Eotf.PQ}   # HDR PQ with default metadata
    )

    if success:
        print("Successfully displaying HDR frame")
        print("Press Ctrl+C to stop...")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
    else:
        print("Failed to display frame")

    # Cleanup
    output.stop()
    output.cleanup()


def example_with_custom_metadata():
    """Example with custom HDR metadata values"""
    output = bmo.BlackmagicOutput()

    if not output.initialize(device_index=0):
        print("Failed to initialize DeckLink device")
        return

    # Create test frame
    width, height = 1920, 1080
    frame = np.ones((height, width, 3), dtype=np.float32) * 0.5

    # Create custom HDR metadata
    import decklink_output as dl
    custom = dl.HdrMetadataCustom()
    custom.display_primaries_red_x = 0.68
    custom.display_primaries_red_y = 0.32
    custom.display_primaries_green_x = 0.265
    custom.display_primaries_green_y = 0.69
    custom.display_primaries_blue_x = 0.15
    custom.display_primaries_blue_y = 0.06
    custom.white_point_x = 0.3127
    custom.white_point_y = 0.3290
    custom.max_mastering_luminance = 1000.0
    custom.min_mastering_luminance = 0.0001
    custom.max_content_light_level = 1000.0
    custom.max_frame_average_light_level = 400.0

    # Display with custom metadata
    success = output.display_static_frame(
        frame,
        bmo.DisplayMode.HD1080p25,
        pixel_format=bmo.PixelFormat.YUV10,
        matrix=bmo.Matrix.Rec2020,
        hdr_metadata={
            'eotf': bmo.Eotf.PQ,
            'custom': custom
        }
    )

    if success:
        print("Displaying with custom HDR metadata")
        print("Press Ctrl+C to stop...")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")

    output.stop()
    output.cleanup()


if __name__ == "__main__":
    main()
    # Uncomment to try custom metadata:
    example_with_custom_metadata()
