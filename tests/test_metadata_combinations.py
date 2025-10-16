#!/usr/bin/env python3
"""
Test various EOTF/Matrix combinations to verify metadata is correctly set.
Displays color bars for 5 seconds in each configuration.
Run pixel_reader in another window to verify the metadata.
"""

import time
import sys

import blackmagic_output as bmo


def main():
    output = bmo.BlackmagicOutput()

    if not output.initialize():
        print("Failed to initialize DeckLink device")
        return 1

    print("DeckLink device initialized successfully\n")

    display_mode = bmo.DisplayMode.HD1080p25
    pixel_format = bmo.PixelFormat.YUV10

    # Get frame dimensions
    info = output.get_display_mode_info(display_mode)
    width = info['width']
    height = info['height']

    # Create test pattern once using built-in function
    frame = bmo.create_test_pattern(width, height, pattern='bars') * 0.75

    # Test configurations
    test_cases = [
        # SDR with different matrices
        # Note: Rec.601 is only supported for SD display modes
        ("SDR + Rec.709", bmo.Matrix.Rec709, None),
        ("SDR + Rec.2020", bmo.Matrix.Rec2020, None),

        # HLG with different matrices
        ("HLG + Rec.709", bmo.Matrix.Rec709, {'eotf': bmo.Eotf.HLG}),
        ("HLG + Rec.2020", bmo.Matrix.Rec2020, {'eotf': bmo.Eotf.HLG}),

        # PQ with different matrices
        ("PQ + Rec.709", bmo.Matrix.Rec709, {'eotf': bmo.Eotf.PQ}),
        ("PQ + Rec.2020", bmo.Matrix.Rec2020, {'eotf': bmo.Eotf.PQ}),

        # Back to SDR to test metadata clearing
        ("SDR + Rec.2020 (after HDR)", bmo.Matrix.Rec2020, None),
        ("SDR + Rec.709 (after HDR)", bmo.Matrix.Rec709, None),
    ]

    print("=" * 60)
    print("Testing EOTF/Matrix Combinations")
    print("=" * 60)
    print(f"Display Mode: {display_mode.name}")
    print(f"Pixel Format: {pixel_format.name}")
    print(f"Duration per test: 5 seconds")
    print("=" * 60)
    print()

    try:
        for i, (label, matrix, hdr_metadata) in enumerate(test_cases, 1):
            print(f"[{i}/{len(test_cases)}] {label}")
            print("-" * 60)

            # Display the frame with the specified configuration
            success = output.display_static_frame(
                frame,
                display_mode,
                pixel_format=pixel_format,
                matrix=matrix,
                hdr_metadata=hdr_metadata
            )

            if not success:
                print(f"  ERROR: Failed to display frame")
                continue

            # Get current output info
            output_info = output.get_current_output_info()
            print(f"  Output: {output_info['display_mode_name']}")
            print(f"  Format: {output_info['pixel_format_name']}")
            print(f"  Matrix: {matrix.name}")
            if hdr_metadata:
                print(f"  EOTF: {hdr_metadata['eotf'].name}")
            else:
                print(f"  EOTF: SDR")
            print()

            # Display for 5 seconds
            time.sleep(5)

        print("=" * 60)
        print("Test completed!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    finally:
        output.stop()
        output.cleanup()

    return 0


if __name__ == '__main__':
    sys.exit(main())
