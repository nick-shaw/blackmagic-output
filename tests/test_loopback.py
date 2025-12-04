#!/usr/bin/env python3
"""Loopback test for all pixel formats.

Requires a BNC cable connecting output to input on the same device.
Tests output -> capture -> conversion for all supported pixel formats.
"""

import decklink_io
from blackmagic_io import create_test_pattern
import numpy as np
import matplotlib.pyplot as plt
import time

def test_pixel_format(output_device, input_device, pixel_format, display_mode, format_name, test_hdr_metadata=False):
    """Test a single pixel format with loopback."""
    print(f"\n{'=' * 70}")
    print(f"Testing {format_name} ({pixel_format})")
    print(f"{'=' * 70}")

    # Get video settings
    settings = output_device.get_video_settings(display_mode)
    width = settings.width
    height = settings.height

    print(f"Resolution: {width}x{height}")
    print(f"Framerate: {settings.framerate} fps")

    # Set HDR metadata if requested
    if test_hdr_metadata:
        print("Setting HDR metadata (PQ, Rec.2020, custom values)...")
        # Create custom HDR metadata
        hdr_metadata = decklink_io.HdrMetadataCustom()
        # Display primaries (Rec.2020)
        hdr_metadata.display_primaries_red_x = 0.708
        hdr_metadata.display_primaries_red_y = 0.292
        hdr_metadata.display_primaries_green_x = 0.170
        hdr_metadata.display_primaries_green_y = 0.797
        hdr_metadata.display_primaries_blue_x = 0.131
        hdr_metadata.display_primaries_blue_y = 0.046
        # White point (D65)
        hdr_metadata.white_point_x = 0.3127
        hdr_metadata.white_point_y = 0.3290
        # Mastering display luminance
        hdr_metadata.max_display_mastering_luminance = 1000.0  # 1000 nits
        hdr_metadata.min_display_mastering_luminance = 0.005   # 0.005 nits
        # Content light level
        hdr_metadata.max_content_light_level = 800.0           # 800 nits
        hdr_metadata.max_frame_average_light_level = 400.0     # 400 nits

        output_device.set_hdr_metadata_custom(
            decklink_io.Gamut.Rec2020,
            decklink_io.Eotf.PQ,
            hdr_metadata
        )

    # Setup output
    settings.format = pixel_format
    if not output_device.setup_output(settings):
        print(f"ERROR: Failed to setup output for {format_name}")
        return False

    # Create test pattern (RGB float, 75% intensity to avoid clipping)
    rgb_pattern = create_test_pattern(width, height, pattern='bars') * 0.75

    # Convert to appropriate format
    if pixel_format == decklink_io.PixelFormat.BGRA:
        # Convert float RGB to BGRA uint8 (hardware converts to YUV8)
        # Use proper rounding for float→uint8 conversion
        rgb_uint8 = np.round(rgb_pattern * 255).astype(np.uint8)
        frame_data = decklink_io.rgb_to_bgra(
            rgb_uint8,
            width, height
        )
    elif pixel_format == decklink_io.PixelFormat.YUV8:
        # Convert to YUV8 directly (2vuy format)
        # Use proper rounding for float→uint8 conversion
        rgb_uint8 = np.round(rgb_pattern * 255).astype(np.uint8)
        frame_data = decklink_io.rgb_uint8_to_yuv8(
            rgb_uint8, width, height,
            matrix=decklink_io.Gamut.Rec709
        )
    elif pixel_format == decklink_io.PixelFormat.YUV10:
        # Convert to YUV10
        # Use proper rounding for float→uint16 conversion
        rgb_uint16 = np.round(rgb_pattern * 65535).astype(np.uint16)
        frame_data = decklink_io.rgb_uint16_to_yuv10(
            rgb_uint16, width, height,
            matrix=decklink_io.Gamut.Rec709,
            input_narrow_range=False,
            output_narrow_range=True
        )
    elif pixel_format == decklink_io.PixelFormat.RGB10:
        # Convert to RGB10 with narrow range for exact code values
        frame_data = decklink_io.rgb_float_to_rgb10(
            rgb_pattern, width, height,
            output_narrow_range=True
        )
    elif pixel_format == decklink_io.PixelFormat.RGB12:
        # Convert to RGB12 using narrow range for exact code values with 75% bars
        # Narrow range: 10-bit (64-940) and 12-bit (256-3760) align perfectly (4x scaling)
        frame_data = decklink_io.rgb_float_to_rgb12(
            rgb_pattern, width, height,
            output_narrow_range=True
        )
    else:
        print(f"ERROR: Unsupported pixel format: {pixel_format}")
        return False

    # Set frame data and start output
    if not output_device.set_frame_data(frame_data):
        print(f"ERROR: Failed to set frame data for {format_name}")
        return False

    print("Starting output...")
    if not output_device.display_frame():
        print(f"ERROR: Failed to display frame for {format_name}")
        return False

    # Wait for signal to stabilize
    time.sleep(0.5)

    # Start capture
    print("Starting capture...")
    if not input_device.start_capture():
        print(f"ERROR: Failed to start capture for {format_name}")
        output_device.stop_output()
        return False

    # Capture frame
    print("Capturing frame...")
    captured_frame = decklink_io.CapturedFrame()
    if not input_device.capture_frame(captured_frame, 10000):
        print(f"ERROR: Failed to capture frame for {format_name}")
        input_device.stop_capture()
        output_device.stop_output()
        return False

    print(f"Captured frame:")
    print(f"  Format: {captured_frame.format}")
    print(f"  Size: {captured_frame.width}x{captured_frame.height}")
    print(f"  Data size: {len(captured_frame.data)} bytes")
    print(f"  Colorspace: {captured_frame.colorspace}")
    print(f"  EOTF: {captured_frame.eotf}")

    # Verify HDR metadata if it was set
    if test_hdr_metadata:
        print("\n--- HDR Metadata Verification ---")
        metadata_passed = True

        # Check EOTF and colorspace
        if captured_frame.eotf != decklink_io.Eotf.PQ:
            print(f"  ✗ EOTF mismatch: expected PQ, got {captured_frame.eotf}")
            metadata_passed = False
        else:
            print(f"  ✓ EOTF: {captured_frame.eotf}")

        if captured_frame.colorspace != decklink_io.Gamut.Rec2020:
            print(f"  ✗ Colorspace mismatch: expected Rec2020, got {captured_frame.colorspace}")
            metadata_passed = False
        else:
            print(f"  ✓ Colorspace: {captured_frame.colorspace}")

        # Check display primaries
        if captured_frame.has_display_primaries:
            print(f"  ✓ Display primaries present:")
            print(f"    Red:   ({captured_frame.display_primaries_red_x:.4f}, {captured_frame.display_primaries_red_y:.4f})")
            print(f"    Green: ({captured_frame.display_primaries_green_x:.4f}, {captured_frame.display_primaries_green_y:.4f})")
            print(f"    Blue:  ({captured_frame.display_primaries_blue_x:.4f}, {captured_frame.display_primaries_blue_y:.4f})")
            # Verify values (allow small tolerance for rounding)
            tolerance = 0.0001
            if abs(captured_frame.display_primaries_red_x - 0.708) > tolerance or \
               abs(captured_frame.display_primaries_red_y - 0.292) > tolerance:
                print(f"    ✗ Red primary mismatch (expected 0.708, 0.292)")
                metadata_passed = False
        else:
            print(f"  ✗ Display primaries missing")
            metadata_passed = False

        # Check white point
        if captured_frame.has_white_point:
            print(f"  ✓ White point: ({captured_frame.white_point_x:.4f}, {captured_frame.white_point_y:.4f})")
            tolerance = 0.0001
            if abs(captured_frame.white_point_x - 0.3127) > tolerance or \
               abs(captured_frame.white_point_y - 0.3290) > tolerance:
                print(f"    ✗ White point mismatch (expected 0.3127, 0.3290)")
                metadata_passed = False
        else:
            print(f"  ✗ White point missing")
            metadata_passed = False

        # Check mastering luminance
        if captured_frame.has_mastering_luminance:
            print(f"  ✓ Mastering luminance:")
            print(f"    Max: {captured_frame.max_display_mastering_luminance:.1f} nits")
            print(f"    Min: {captured_frame.min_display_mastering_luminance:.4f} nits")
            if abs(captured_frame.max_display_mastering_luminance - 1000.0) > 1.0 or \
               abs(captured_frame.min_display_mastering_luminance - 0.005) > 0.001:
                print(f"    ✗ Mastering luminance mismatch (expected 1000.0, 0.005)")
                metadata_passed = False
        else:
            print(f"  ✗ Mastering luminance missing")
            metadata_passed = False

        # Check content light level
        if captured_frame.has_max_cll:
            print(f"  ✓ Max content light level: {captured_frame.max_content_light_level:.1f} nits")
            if abs(captured_frame.max_content_light_level - 800.0) > 1.0:
                print(f"    ✗ MaxCLL mismatch (expected 800.0)")
                metadata_passed = False
        else:
            print(f"  ✗ Max content light level missing")
            metadata_passed = False

        if captured_frame.has_max_fall:
            print(f"  ✓ Max frame average light level: {captured_frame.max_frame_average_light_level:.1f} nits")
            if abs(captured_frame.max_frame_average_light_level - 400.0) > 1.0:
                print(f"    ✗ MaxFALL mismatch (expected 400.0)")
                metadata_passed = False
        else:
            print(f"  ✗ Max frame average light level missing")
            metadata_passed = False

        if not metadata_passed:
            print("\n  ✗ HDR Metadata verification FAILED")
            input_device.stop_capture()
            output_device.stop_output()
            return False
        else:
            print("\n  ✓ HDR Metadata verification PASSED")

    # Convert captured frame to RGB for display
    if captured_frame.format == decklink_io.PixelFormat.YUV8:
        print("Converting YUV8 to RGB...")
        rgb_captured = decklink_io.yuv8_to_rgb_float(
            np.array(captured_frame.data, dtype=np.uint8),
            captured_frame.width,
            captured_frame.height,
            matrix=captured_frame.colorspace,
            input_narrow_range=True
        )
    elif captured_frame.format == decklink_io.PixelFormat.YUV10:
        print("Converting YUV10 to RGB...")
        rgb_captured = decklink_io.yuv10_to_rgb_float(
            np.array(captured_frame.data, dtype=np.uint8),
            captured_frame.width,
            captured_frame.height,
            matrix=captured_frame.colorspace,
            input_narrow_range=True
        )
    elif captured_frame.format == decklink_io.PixelFormat.RGB10:
        print("Converting RGB10 to RGB...")
        rgb_captured = decklink_io.rgb10_to_float(
            np.array(captured_frame.data, dtype=np.uint8),
            captured_frame.width,
            captured_frame.height,
            input_narrow_range=True
        )
    elif captured_frame.format == decklink_io.PixelFormat.RGB12:
        print("Converting RGB12 to RGB...")
        rgb_captured = decklink_io.rgb12_to_float(
            np.array(captured_frame.data, dtype=np.uint8),
            captured_frame.width,
            captured_frame.height,
            input_narrow_range=True
        )
    elif captured_frame.format == decklink_io.PixelFormat.BGRA:
        print("Converting BGRA to RGB...")
        bgra_data = np.frombuffer(captured_frame.data, dtype=np.uint8).reshape(
            (captured_frame.height, captured_frame.width, 4)
        )
        rgb_captured = np.zeros((captured_frame.height, captured_frame.width, 3), dtype=np.float32)
        rgb_captured[:, :, 0] = bgra_data[:, :, 2] / 255.0  # R
        rgb_captured[:, :, 1] = bgra_data[:, :, 1] / 255.0  # G
        rgb_captured[:, :, 2] = bgra_data[:, :, 0] / 255.0  # B
    else:
        print(f"ERROR: Unsupported pixel format for conversion: {captured_frame.format}")
        input_device.stop_capture()
        output_device.stop_output()
        return False

    # Compare source to captured
    print("\n--- Verification ---")

    # Calculate errors
    diff = np.abs(rgb_pattern - rgb_captured)
    mean_error = np.mean(diff)
    max_error = np.max(diff)

    # Calculate per-channel errors
    r_error = np.mean(diff[:, :, 0])
    g_error = np.mean(diff[:, :, 1])
    b_error = np.mean(diff[:, :, 2])

    print(f"  Mean error: {mean_error:.6f}")
    print(f"  Max error: {max_error:.6f}")
    print(f"  Per-channel mean error - R: {r_error:.6f}, G: {g_error:.6f}, B: {b_error:.6f}")

    # For 4:2:2 formats, expect higher chroma error
    is_422 = captured_frame.format in [
        decklink_io.PixelFormat.YUV8,
        decklink_io.PixelFormat.YUV10
    ]

    # Set acceptable thresholds
    if captured_frame.format == decklink_io.PixelFormat.YUV8:
        # YUV8 has higher error due to:
        # - 8-bit quantization (256 levels vs 1024/4096 for 10/12-bit)
        # - 4:2:2 chroma subsampling
        # Both BGRA→YUV8 hardware and direct YUV8 show similar error characteristics
        acceptable_mean = 0.10  # 10% average error
        acceptable_max = 0.35   # 35% max error
    elif is_422:
        # 10-bit 4:2:2 formats have chroma subsampling but better precision
        acceptable_mean = 0.02  # 2% average error
        acceptable_max = 0.15   # 15% max error
    else:
        # RGB formats should be perfect (zero error) with proper rounding
        # and narrow range alignment
        acceptable_mean = 0.01  # 1% average error
        acceptable_max = 0.05   # 5% max error

    # Check if errors are acceptable
    passed = mean_error < acceptable_mean and max_error < acceptable_max

    if passed:
        print(f"  ✓ Verification PASSED (mean < {acceptable_mean}, max < {acceptable_max})")
    else:
        print(f"  ✗ Verification FAILED (mean threshold: {acceptable_mean}, max threshold: {acceptable_max})")

    # Display side-by-side comparison
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

    ax1.imshow(rgb_pattern)
    ax1.set_title("Source Pattern")
    ax1.axis('off')

    ax2.imshow(rgb_captured)
    ax2.set_title(f"Captured: {format_name}\n({captured_frame.colorspace})")
    ax2.axis('off')

    # Show difference (amplified for visibility)
    diff_amplified = np.clip(diff * 10, 0, 1)
    ax3.imshow(diff_amplified)
    ax3.set_title(f"Difference (10x)\nMean: {mean_error:.4f}, Max: {max_error:.4f}")
    ax3.axis('off')

    plt.tight_layout()
    plt.show()

    # Cleanup
    input_device.stop_capture()
    output_device.stop_output()

    if passed:
        print(f"✓ {format_name} test PASSED!")
    else:
        print(f"✗ {format_name} test FAILED!")

    return passed

def main():
    """Run loopback tests for all pixel formats."""
    print("Blackmagic Loopback Test")
    print("=" * 70)
    print("This test requires a BNC cable connecting output to input")
    print("on the same UltraStudio 4K Mini device.")
    print("=" * 70)

    # Create output and input devices
    output_device = decklink_io.DeckLinkOutput()
    input_device = decklink_io.DeckLinkInput()

    # Initialize devices (using device 0)
    print("\nInitializing output device...")
    if not output_device.initialize(0):
        print("ERROR: Failed to initialize output device")
        return 1

    print("Initializing input device...")
    if not input_device.initialize(0):
        print("ERROR: Failed to initialize input device")
        output_device.cleanup()
        return 1

    # Use HD1080p25 mode for testing
    display_mode = decklink_io.DisplayMode.HD1080p25

    # Test all formats: BGRA (→YUV8 in hardware), YUV8 (direct), YUV10, RGB10, RGB12
    # RGB10 includes HDR metadata verification
    test_formats = [
        (decklink_io.PixelFormat.BGRA, "8-bit BGRA (→YUV8 hardware)", False),
        (decklink_io.PixelFormat.YUV8, "8-bit YUV (2vuy direct)", False),
        (decklink_io.PixelFormat.YUV10, "10-bit YUV (v210)", False),
        (decklink_io.PixelFormat.RGB10, "10-bit RGB (R10l) + HDR metadata", True),
        (decklink_io.PixelFormat.RGB12, "12-bit RGB (R12L)", False),
    ]

    results = []
    for pixel_format, format_name, test_hdr in test_formats:
        success = test_pixel_format(
            output_device, input_device,
            pixel_format, display_mode, format_name, test_hdr
        )
        results.append((format_name, success))

    # Cleanup
    input_device.cleanup()
    output_device.cleanup()

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for format_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {format_name}")

    all_passed = all(success for _, success in results)
    print("=" * 70)
    if all_passed:
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1

if __name__ == "__main__":
    exit(main())
